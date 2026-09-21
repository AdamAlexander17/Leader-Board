from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
from datetime import datetime
import csv
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from db.database import get_db
from services import leaderboard_service

router = APIRouter()


@router.get("/leaderboard")
def leaderboard(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Get paginated leaderboard."""
    return leaderboard_service.get_leaderboard(db, page=page, page_size=page_size)


@router.get("/rank/{user_id}")
def find_rank(user_id: int, db: Session = Depends(get_db)):
    """Find a user's rank by user_id."""
    result = leaderboard_service.get_user_rank(db, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.get("/search")
def search(q: str = Query(..., description="Account ID or Username"), db: Session = Depends(get_db)):
    """Search user by account_id or username."""
    result = leaderboard_service.search_user(db, q)
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.post("/sync")
async def manual_sync(db: Session = Depends(get_db)):
    """Manual sync is disabled to prevent external API updates."""
    raise HTTPException(status_code=503, detail="External API sync is disabled")


@router.get("/export-excel")
def export_excel(db: Session = Depends(get_db)):
    """Export leaderboard data up to today 11:59 PM as Excel file."""
    start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
    data = leaderboard_service.get_leaderboard_data_for_range(db, start_dt, end_dt)
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Leaderboard"
    
    # Define headers
    headers = ["Rank", "First Name", "Last Name", "Account ID", "User ID", "Username", "Balance", "Equity", "Current PnL"]
    
    # Add headers with styling
    header_fill = PatternFill(start_color="b8ff00", end_color="b8ff00", fill_type="solid")
    header_font = Font(bold=True, color="0a0a0a", size=12)
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
    
    # Add data rows
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    for row_num, user in enumerate(data, 2):
        ws.cell(row=row_num, column=1).value = user["rank"]
        ws.cell(row=row_num, column=2).value = user["first_name"]
        ws.cell(row=row_num, column=3).value = user["last_name"]
        ws.cell(row=row_num, column=4).value = user["account_id"]
        ws.cell(row=row_num, column=5).value = user["user_id"]
        ws.cell(row=row_num, column=6).value = user["username"]
        ws.cell(row=row_num, column=7).value = user["balance"]
        ws.cell(row=row_num, column=8).value = user["equity"]
        ws.cell(row=row_num, column=9).value = user["current_pnl"]
        
        # Apply border and alignment to all cells
        for col_num in range(1, 10):
            cell = ws.cell(row=row_num, column=col_num)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Add border to header
    for col_num in range(1, 10):
        ws.cell(row=1, column=col_num).border = thin_border
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 10
    ws.column_dimensions['B'].width = 18
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 10
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 15
    ws.column_dimensions['I'].width = 15
    
    # Save to bytes buffer
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"leaderboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export-csv")
def export_csv(db: Session = Depends(get_db)):
    """Export leaderboard data up to today 11:59 PM as CSV file."""
    start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
    data = leaderboard_service.get_leaderboard_data_for_range(db, start_dt, end_dt)
    
    # Create CSV in memory with UTF-8 encoding
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = ["Rank", "First Name", "Last Name", "Account ID", "User ID", "Username", "Balance", "Equity", "Current PnL"]
    writer.writerow(headers)
    
    # Write data rows
    for user in data:
        writer.writerow([
            user["rank"],
            user["first_name"],
            user["last_name"],
            user["account_id"],
            user["user_id"],
            user["username"],
            user["balance"],
            user["equity"],
            user["current_pnl"]
        ])
    
    output.seek(0)
    filename = f"leaderboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
