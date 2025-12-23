from typing import Dict, Any, List
from openai import AzureOpenAI
from core.config import settings
from core.logger import logger
from database.postgres_db import get_db, Sales, Batches, BatchStockTracking, SpoilageReport, Perishable, ProductHierarchy, LocationDimension
from sqlalchemy import desc, func, and_, or_
from datetime import datetime, timedelta


class InventoryAgent:
    """Agent specialized in inventory analysis: batch tracking, spoilage, sales transactions, and stock movements"""
    
    # Static current date context (Nov 8, 2025)
    CURRENT_WEEKEND_DATE = "2025-11-08"
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.OPENAI_ENDPOINT
        )
        self.system_prompt = """You are an inventory management expert for RETAIL SUPPLY CHAIN operations.

=== CURRENT DATE CONTEXT ===
This Weekend (Current Week End Date): November 8, 2025 (2025-11-08)
- "Next week" = November 15, 2025 | "Last week" = November 1, 2025
- "Next month" = December 2025 | "Last month" = October 2025
- Current Year: 2025 | Last Year (LY): 2024

=== YOUR SPECIALIZATIONS ===
1. BATCH EXPIRY TRACKING
   - Monitor batches expiring within next 7/14/30 days
   - Track shelf life for perishable goods
   - Identify products at risk of waste due to expiry
   
2. SPOILAGE ANALYSIS
   - Analyze spoilage patterns by product, store, and reason
   - Calculate spoilage rates and financial impact
   - Identify root causes: temperature, handling, shelf life issues
   - Recommend waste reduction strategies
   
3. SALES TRANSACTION ANALYSIS
   - Analyze sales velocity by batch
   - Track revenue and units sold per product/store
   - Identify slow-moving vs fast-moving inventory
   
4. STOCK MOVEMENT TRACKING
   - Monitor transfers, adjustments, and returns
   - Track opening/closing balances weekly
   - Identify discrepancies and reconciliation needs
   
5. INVENTORY OPTIMIZATION
   - For perishable products especially
   - Balance stock levels vs expiry risk
   - Recommend reorder points based on velocity

=== KEY DATASETS ===
- Sales: Transactional sales data (units sold, revenue, discounts)
- Batches: Batch records (expiry dates, quantities, lifecycle)
- Batch Stock Tracking: Weekly stock movements (inflows, balances)
- Spoilage Report: Waste tracking (quantities, reasons, percentages)

Provide actionable insights with specific numbers, dates, and recommendations."""
    
    def analyze(self, query: str, product_id: str = None, location_id: str = None) -> Dict[str, Any]:
        """Main analysis dispatcher - routes to specific analysis based on query type"""
        try:
            print("\n" + "="*80)
            print("📦 INVENTORY AGENT - Batch, Spoilage & Sales Analysis")
            print("="*80)
            
            query_lower = query.lower()
            
            # Route to specialized analysis
            if any(keyword in query_lower for keyword in ["expir", "batch", "shelf life", "expir"]):
                return self.analyze_batch_expiry(query, product_id, location_id)
            
            elif any(keyword in query_lower for keyword in ["spoil", "waste", "loss", "damage"]):
                return self.analyze_spoilage(query, product_id, location_id)
            
            elif any(keyword in query_lower for keyword in ["sales transaction", "batch sale", "revenue by batch"]):
                return self.analyze_sales_transactions(query, product_id, location_id)
            
            elif any(keyword in query_lower for keyword in ["movement", "transfer", "adjustment", "stock tracking"]):
                return self.track_stock_movements(query, product_id, location_id)
            
            else:
                # Default: comprehensive inventory overview
                return self.inventory_overview(query, product_id, location_id)
                
        except Exception as e:
            logger.error(f"Inventory analysis failed: {e}")
            return {"agent": "inventory", "status": "error", "message": str(e)}
    
    def analyze_batch_expiry(self, query: str, product_id: str = None, location_id: str = None) -> Dict[str, Any]:
        """Analyze batches expiring soon"""
        try:
            with get_db() as db:
                # Use static current date (Nov 8, 2025) instead of datetime.now()
                today = datetime(2025, 11, 8).date()
                expiry_window = today + timedelta(days=7)
                
                query_filter = and_(
                    Batches.expiry_date.between(today, expiry_window),
                    Batches.current_qty > 0
                )
                
                if product_id:
                    query_filter = and_(query_filter, Batches.product_code.like(f"%{product_id}%"))
                if location_id:
                    query_filter = and_(query_filter, Batches.store_code == location_id)
                
                expiring_batches = db.query(Batches).filter(query_filter).order_by(Batches.expiry_date).limit(50).all()
                
                if not expiring_batches:
                    return {
                        "agent": "inventory",
                        "status": "success",
                        "message": "✅ No batches expiring in next 7 days",
                        "expiring_batches": []
                    }
                
                # Format batch data
                batch_data = [{
                    "batch_id": b.batch_id,
                    "product": b.product_code,
                    "store": b.store_code,
                    "expiry_date": str(b.expiry_date),
                    "days_until_expiry": (b.expiry_date - today).days,
                    "current_qty": float(b.current_qty),
                    "initial_qty": float(b.initial_qty)
                } for b in expiring_batches]
                
                # Calculate summary stats
                total_expiring_qty = sum([float(b.current_qty) for b in expiring_batches])
                unique_products = len(set([b.product_code for b in expiring_batches]))
                unique_stores = len(set([b.store_code for b in expiring_batches]))
                
                context = f"""BATCH EXPIRY ANALYSIS:
                Batches Expiring (Next 7 Days): {len(expiring_batches)}
                Total Quantity at Risk: {total_expiring_qty:.0f} units
                Products Affected: {unique_products}
                Stores Affected: {unique_stores}
                
                Top 10 Expiring Soon:
                {self._format_batch_list(batch_data[:10])}
                """
                
                # Get LLM recommendations
                response = self.client.chat.completions.create(
                    model=settings.OPENAI_MODEL_NAME,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": f"{query}\n\n{context}"}
                    ],
                    max_tokens=600
                )
                
                return {
                    "agent": "inventory",
                    "status": "success",
                    "analysis": response.choices[0].message.content,
                    "expiring_batches": batch_data,
                    "total_batches": len(expiring_batches),
                    "total_qty_at_risk": total_expiring_qty,
                    "unique_products": unique_products,
                    "unique_stores": unique_stores
                }
                
        except Exception as e:
            logger.error(f"Batch expiry analysis failed: {e}")
            return {"agent": "inventory", "status": "error", "message": str(e)}
    
    def analyze_spoilage(self, query: str, product_id: str = None, location_id: str = None) -> Dict[str, Any]:
        """Analyze spoilage patterns and waste"""
        try:
            with get_db() as db:
                # Use static current date (Nov 8, 2025) - get last 30 days
                cutoff_date = datetime(2025, 11, 8).date() - timedelta(days=30)
                
                query_filter = SpoilageReport.report_date >= cutoff_date
                
                if product_id:
                    query_filter = and_(query_filter, SpoilageReport.product_code.like(f"%{product_id}%"))
                if location_id:
                    query_filter = and_(query_filter, SpoilageReport.store_code == location_id)
                
                spoilage_records = db.query(SpoilageReport).filter(query_filter).order_by(desc(SpoilageReport.spoilage_qty)).limit(100).all()
                
                if not spoilage_records:
                    return {
                        "agent": "inventory",
                        "status": "success",
                        "message": "✅ No spoilage reported in last 30 days",
                        "spoilage_data": []
                    }
                
                # Calculate summary stats
                total_spoilage_qty = sum([float(s.spoilage_qty) for s in spoilage_records])
                avg_spoilage_pct = sum([float(s.spoilage_pct) for s in spoilage_records]) / len(spoilage_records)
                
                # Severity breakdown
                severity_counts = {}
                for s in spoilage_records:
                    case = s.spoilage_case or "Unknown"
                    severity_counts[case] = severity_counts.get(case, 0) + 1
                
                # Top products by spoilage
                product_spoilage = {}
                for s in spoilage_records:
                    prod = s.product_code
                    product_spoilage[prod] = product_spoilage.get(prod, 0) + float(s.spoilage_qty)
                
                top_products = sorted(product_spoilage.items(), key=lambda x: x[1], reverse=True)[:10]
                
                # Top stores by spoilage
                store_spoilage = {}
                for s in spoilage_records:
                    store = s.store_code
                    store_spoilage[store] = store_spoilage.get(store, 0) + float(s.spoilage_qty)
                
                top_stores = sorted(store_spoilage.items(), key=lambda x: x[1], reverse=True)[:10]
                
                context = f"""SPOILAGE ANALYSIS (Last 30 Days):
                Total Spoilage Reports: {len(spoilage_records)}
                Total Quantity Spoiled: {total_spoilage_qty:.0f} units
                Average Spoilage %: {avg_spoilage_pct:.2f}%
                
                Severity Breakdown:
                {self._format_dict_list(severity_counts)}
                
                Top 10 Products by Spoilage:
                {self._format_tuple_list(top_products)}
                
                Top 10 Stores by Spoilage:
                {self._format_tuple_list(top_stores)}
                """
                
                # Get LLM recommendations
                response = self.client.chat.completions.create(
                    model=settings.OPENAI_MODEL_NAME,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": f"{query}\n\n{context}"}
                    ],
                    max_tokens=700
                )
                
                return {
                    "agent": "inventory",
                    "status": "success",
                    "analysis": response.choices[0].message.content,
                    "total_spoilage_qty": total_spoilage_qty,
                    "avg_spoilage_pct": avg_spoilage_pct,
                    "severity_breakdown": severity_counts,
                    "top_products": dict(top_products),
                    "top_stores": dict(top_stores),
                    "record_count": len(spoilage_records)
                }
                
        except Exception as e:
            logger.error(f"Spoilage analysis failed: {e}")
            return {"agent": "inventory", "status": "error", "message": str(e)}
    
    def analyze_sales_transactions(self, query: str, product_id: str = None, location_id: str = None) -> Dict[str, Any]:
        """Analyze sales transactions by batch"""
        try:
            with get_db() as db:
                # Use static current date (Nov 8, 2025) - get last 30 days
                cutoff_date = datetime(2025, 11, 8).date() - timedelta(days=30)
                
                query_filter = Sales.sale_date >= cutoff_date
                
                if product_id:
                    query_filter = and_(query_filter, Sales.product_code.like(f"%{product_id}%"))
                if location_id:
                    query_filter = and_(query_filter, Sales.store_code == location_id)
                
                sales_records = db.query(Sales).filter(query_filter).order_by(desc(Sales.revenue)).limit(200).all()
                
                if not sales_records:
                    return {
                        "agent": "inventory",
                        "status": "success",
                        "message": "No sales transactions in last 30 days",
                        "sales_data": []
                    }
                
                # Calculate summary stats
                total_revenue = sum([float(s.revenue) for s in sales_records])
                total_quantity = sum([float(s.quantity_sold) for s in sales_records])
                avg_transaction_value = total_revenue / len(sales_records)
                
                # Sales by product
                product_revenue = {}
                for s in sales_records:
                    prod = s.product_code
                    product_revenue[prod] = product_revenue.get(prod, 0) + float(s.revenue)
                
                top_products = sorted(product_revenue.items(), key=lambda x: x[1], reverse=True)[:10]
                
                # Sales by store
                store_revenue = {}
                for s in sales_records:
                    store = s.store_code
                    store_revenue[store] = store_revenue.get(store, 0) + float(s.revenue)
                
                top_stores = sorted(store_revenue.items(), key=lambda x: x[1], reverse=True)[:10]
                
                context = f"""SALES TRANSACTION ANALYSIS (Last 30 Days):
                Total Transactions: {len(sales_records)}
                Total Revenue: ${total_revenue:,.2f}
                Total Units Sold: {total_quantity:.0f}
                Average Transaction Value: ${avg_transaction_value:.2f}
                
                Top 10 Products by Revenue:
                {self._format_tuple_list(top_products, is_currency=True)}
                
                Top 10 Stores by Revenue:
                {self._format_tuple_list(top_stores, is_currency=True)}
                """
                
                # Get LLM recommendations
                response = self.client.chat.completions.create(
                    model=settings.OPENAI_MODEL_NAME,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": f"{query}\n\n{context}"}
                    ],
                    max_tokens=600
                )
                
                return {
                    "agent": "inventory",
                    "status": "success",
                    "analysis": response.choices[0].message.content,
                    "total_revenue": total_revenue,
                    "total_quantity": total_quantity,
                    "avg_transaction_value": avg_transaction_value,
                    "top_products": dict(top_products),
                    "top_stores": dict(top_stores),
                    "transaction_count": len(sales_records)
                }
                
        except Exception as e:
            logger.error(f"Sales transaction analysis failed: {e}")
            return {"agent": "inventory", "status": "error", "message": str(e)}
    
    def track_stock_movements(self, query: str, product_id: str = None, location_id: str = None) -> Dict[str, Any]:
        """Track inventory movements (transfers, adjustments, spoilage)"""
        try:
            with get_db() as db:
                # Use static current date (Nov 8, 2025) - get last 30 days
                cutoff_date = datetime(2025, 11, 8).date() - timedelta(days=30)
                
                query_filter = BatchStockTracking.transaction_date >= cutoff_date
                
                if product_id:
                    query_filter = and_(query_filter, BatchStockTracking.product_code.like(f"%{product_id}%"))
                if location_id:
                    query_filter = and_(query_filter, BatchStockTracking.store_code == location_id)
                
                movements = db.query(BatchStockTracking).filter(query_filter).order_by(desc(BatchStockTracking.transaction_date)).limit(200).all()
                
                if not movements:
                    return {
                        "agent": "inventory",
                        "status": "success",
                        "message": "No stock movements in last 30 days",
                        "movements": []
                    }
                
                # Transaction type breakdown
                transaction_summary = {}
                transaction_qty = {}
                for m in movements:
                    tx_type = m.transaction_type
                    transaction_summary[tx_type] = transaction_summary.get(tx_type, 0) + 1
                    transaction_qty[tx_type] = transaction_qty.get(tx_type, 0) + float(m.quantity)
                
                # Most active batches
                batch_activity = {}
                for m in movements:
                    batch = m.batch_id
                    batch_activity[batch] = batch_activity.get(batch, 0) + 1
                
                top_batches = sorted(batch_activity.items(), key=lambda x: x[1], reverse=True)[:10]
                
                context = f"""STOCK MOVEMENT ANALYSIS (Last 30 Days):
                Total Movements: {len(movements)}
                
                Transaction Type Breakdown:
                {self._format_transaction_breakdown(transaction_summary, transaction_qty)}
                
                Most Active Batches (by transaction count):
                {self._format_tuple_list(top_batches)}
                """
                
                # Get LLM recommendations
                response = self.client.chat.completions.create(
                    model=settings.OPENAI_MODEL_NAME,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": f"{query}\n\n{context}"}
                    ],
                    max_tokens=600
                )
                
                return {
                    "agent": "inventory",
                    "status": "success",
                    "analysis": response.choices[0].message.content,
                    "transaction_summary": transaction_summary,
                    "transaction_qty": transaction_qty,
                    "top_batches": dict(top_batches),
                    "movement_count": len(movements)
                }
                
        except Exception as e:
            logger.error(f"Stock movement tracking failed: {e}")
            return {"agent": "inventory", "status": "error", "message": str(e)}
    
    def inventory_overview(self, query: str, product_id: str = None, location_id: str = None) -> Dict[str, Any]:
        """Comprehensive inventory overview"""
        try:
            # Get data from multiple analyses
            expiry_data = self.analyze_batch_expiry(query, product_id, location_id)
            spoilage_data = self.analyze_spoilage(query, product_id, location_id)
            sales_data = self.analyze_sales_transactions(query, product_id, location_id)
            
            context = f"""COMPREHENSIVE INVENTORY OVERVIEW:
            
            BATCH EXPIRY STATUS:
            - Batches expiring (7 days): {expiry_data.get('total_batches', 0)}
            - Quantity at risk: {expiry_data.get('total_qty_at_risk', 0):.0f} units
            
            SPOILAGE STATUS (30 days):
            - Total spoilage: {spoilage_data.get('total_spoilage_qty', 0):.0f} units
            - Average spoilage %: {spoilage_data.get('avg_spoilage_pct', 0):.2f}%
            
            SALES PERFORMANCE (30 days):
            - Total revenue: ${sales_data.get('total_revenue', 0):,.2f}
            - Total units sold: {sales_data.get('total_quantity', 0):.0f}
            - Transactions: {sales_data.get('transaction_count', 0)}
            """
            
            # Get LLM summary
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"{query}\n\n{context}"}
                ],
                max_tokens=700
            )
            
            return {
                "agent": "inventory",
                "status": "success",
                "analysis": response.choices[0].message.content,
                "expiry_summary": expiry_data,
                "spoilage_summary": spoilage_data,
                "sales_summary": sales_data
            }
            
        except Exception as e:
            logger.error(f"Inventory overview failed: {e}")
            return {"agent": "inventory", "status": "error", "message": str(e)}
    
    # Helper formatting methods
    def _format_batch_list(self, batches: List[Dict]) -> str:
        """Format batch list for display"""
        lines = []
        for b in batches:
            lines.append(f"  - {b['batch_id']}: {b['product']} @ {b['store']} | Expires: {b['expiry_date']} ({b['days_until_expiry']} days) | Qty: {b['current_qty']:.0f}")
        return "\n".join(lines)
    
    def _format_dict_list(self, data: Dict) -> str:
        """Format dictionary as list"""
        lines = []
        for key, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  - {key}: {value}")
        return "\n".join(lines)
    
    def _format_tuple_list(self, data: List[tuple], is_currency: bool = False) -> str:
        """Format tuple list"""
        lines = []
        for item, value in data:
            if is_currency:
                lines.append(f"  - {item}: ${value:,.2f}")
            else:
                lines.append(f"  - {item}: {value:.0f}")
        return "\n".join(lines)
    
    def _format_transaction_breakdown(self, counts: Dict, quantities: Dict) -> str:
        """Format transaction type breakdown"""
        lines = []
        for tx_type in sorted(counts.keys()):
            count = counts.get(tx_type, 0)
            qty = quantities.get(tx_type, 0)
            lines.append(f"  - {tx_type}: {count} transactions, {qty:.0f} units")
        return "\n".join(lines)

