# File: backend/app/services/token_service.py
# This service will handle token transactions with proper JSON serialization

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

from app.models import User, Transaction, TokenPackage
from app.schemas.transaction import TransactionCreate
from app.crud.transaction import transaction as transaction_crud

class TokenService:
    def update_token_balance(
        self,
        db: Session,
        user_id: int,
        amount: int,
        transaction_type: str = "system",
        description: str = None
    ) -> Dict[str, Any]:
        """
        Update user token balance with proper JSON serialization
        
        Args:
            db: Database session
            user_id: User ID
            amount: Amount to add (positive) or deduct (negative)
            transaction_type: Type of transaction
            description: Transaction description
            
        Returns:
            Dictionary with result
        """
        # Get the user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "message": "User not found"}
        
        # Calculate new balance
        new_balance = user.token_balance + amount
        if new_balance < 0:
            return {"success": False, "message": "Insufficient token balance"}
        
        # Get current token history as a list
        try:
            if isinstance(user.token_history, str):
                token_history = json.loads(user.token_history)
            else:
                token_history = user.token_history or []
                if not isinstance(token_history, list):
                    token_history = []
        except:
            token_history = []
        
        # Add new entry
        token_history.append({
            "amount": amount,
            "timestamp": datetime.utcnow().isoformat(),
            "balance": new_balance,
            "type": transaction_type,
            "description": description or ("Token update" if amount > 0 else "Token usage")
        })
        
        # Convert to JSON string
        token_history_json = json.dumps(token_history)
        
        # Update using direct SQL to avoid SQLAlchemy's serialization issues
        sql = text("""
            UPDATE users 
            SET token_balance = :balance, 
                token_history = :history, 
                updated_at = :now 
            WHERE id = :user_id
        """)
        
        db.execute(sql, {
            "balance": new_balance,
            "history": token_history_json,
            "now": datetime.utcnow().isoformat(),
            "user_id": user_id
        })
        
        db.commit()
        
        # Create transaction record if needed
        if abs(amount) > 0 and transaction_type != "system":
            transaction_data = TransactionCreate(
                user_id=user_id,
                transaction_type=transaction_type,
                amount=abs(amount),
                status="completed",
                tokens_purchased=amount if amount > 0 else None,
                description=description or ("Token purchase" if amount > 0 else "Token usage")
            )
            transaction_crud.create(db, obj_in=transaction_data)
        
        return {
            "success": True,
            "previous_balance": user.token_balance,
            "new_balance": new_balance,
            "amount": amount
        }
    
    def get_token_packages(self, db: Session, is_active: bool = True) -> List[TokenPackage]:
        """Get available token packages"""
        query = db.query(TokenPackage)
        if is_active:
            query = query.filter(TokenPackage.is_active == True)
        return query.all()
    
    def purchase_tokens(
        self,
        db: Session,
        user_id: int,
        package_id: int,
        payment_method: str,
        payment_reference: str = None
    ) -> Dict[str, Any]:
        """
        Purchase tokens from a package
        
        Args:
            db: Database session
            user_id: User ID
            package_id: Token package ID
            payment_method: Payment method used
            payment_reference: Payment reference (e.g., MPesa receipt)
            
        Returns:
            Dictionary with purchase result
        """
        # Check if user and package exist
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "message": "User not found"}
            
        package = db.query(TokenPackage).filter(TokenPackage.id == package_id).first()
        if not package:
            return {"success": False, "message": "Token package not found"}
            
        if not package.is_active:
            return {"success": False, "message": "Token package is not available"}
        
        # Create transaction record
        transaction_data = TransactionCreate(
            user_id=user_id,
            transaction_type="token_purchase",
            amount=package.price,
            currency=package.currency,
            status="completed",
            payment_method=payment_method,
            mpesa_receipt=payment_reference if payment_method == "mpesa" else None,
            tokens_purchased=package.token_count,
            package_id=package_id,
            description=f"Purchase of {package.token_count} tokens"
        )
        
        transaction = transaction_crud.create(db, obj_in=transaction_data)
        
        # Update user token balance
        result = self.update_token_balance(
            db,
            user_id=user_id,
            amount=package.token_count,
            transaction_type="purchase",
            description=f"Purchase of {package.token_count} tokens"
        )
        
        if not result["success"]:
            # Revert transaction status if token update failed
            transaction.status = "failed"
            db.add(transaction)
            db.commit()
            return result
        
        return {
            "success": True,
            "transaction_id": transaction.id,
            "tokens_purchased": package.token_count,
            "previous_balance": result["previous_balance"],
            "new_balance": result["new_balance"],
            "package": {
                "id": package.id,
                "name": package.name,
                "token_count": package.token_count,
                "price": package.price,
                "currency": package.currency
            }
        }

# Create singleton instance
token_service = TokenService()