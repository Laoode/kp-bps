import io
import csv
import re
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import calendar
from typing import Union, List, Dict, Any
from sqlalchemy import text
import reflex as rx
from reflex import UploadFile
from sqlmodel import Field, String, asc, cast, desc, func, or_, select

# ---------------------------
# Model-Model Baru
# ---------------------------

class Employee(rx.Model, table=True):
    """Model untuk data pegawai."""
    __tablename__ = "employees"
    name: str
    nip: str


class Deduction(rx.Model, table=True):
    """Model untuk jenis potongan."""
    __tablename__ = "deductions"
    name: str


class EmployeeDeduction(rx.Model, table=True):
    """Model untuk data potongan tiap pegawai per periode."""
    __tablename__ = "employee_deductions"
    employee_id: int
    deduction_id: int
    amount: int | None = None
    payment_status: str = "unpaid"  # nilai default 'unpaid'
    payment_type: Union[str, None] = None  # 'cash' atau 'transfer'
    month: int
    year: int
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


# Jika dibutuhkan, model untuk _view data_ (bukan tabel) bisa dibuat secara dinamis
# Contoh: EmployeeDeductionEntry (dipakai untuk menampung hasil join/pivot)
class EmployeeDeductionEntry(rx.Model):
    id: int
    name: str
    nip: str
    arisan: int | None = None
    iuran_dw: int | None = None
    simpanan_wajib_koperasi: int | None = None
    belanja_koperasi: int | None = None
    simpanan_pokok: int | None = None
    kredit_khusus: int | None = None
    kredit_barang: int | None = None
    total_potongan: int | None = None
    date: str | None = None
    status: str | None = None
    payment_type: str | None = None


# ---------------------------
# State (Backend Logic)
# ---------------------------
class MonthValues(rx.Base):
    """Nilai-nilai agregat untuk satu bulan."""
    num_entries: int = 0
    total_payments: int = 10000  # jika diperlukan, misalnya total dari salah satu kolom



class State(rx.State):
    """State aplikasi yang diperbarui untuk menangani data EmployeeDeduction."""
    # Daftar entry hasil join/pivot (untuk front end)
    entries: list[EmployeeDeductionEntry] = []
    sort_value: str = ""
    sort_reverse: bool = False
    search_value: str = ""
    current_entry: EmployeeDeductionEntry = None  # untuk update
    
    # Nilai agregat (bisa disesuaikan jika diperlukan)
    current_month_values: MonthValues = MonthValues()
    previous_month_values: MonthValues = MonthValues()
    
    # Tambahkan variabel untuk pagination
    total_entries: int = 0
    offset: int = 0
    limit: int = 10  # Jumlah baris per halaman
    
    current_month: datetime = datetime.now()  # Untuk tracking bulan aktif
    timeframe: str = "Monthly"
    
    # Tambahkan state variables baru
    selected_employee_id: int = 1
    selected_deduction: str = "Arisan"  # Default deduction
    current_page_month: int = 1  # 1 untuk Jan-Jun, 2 untuk Jul-Dec
    nip_input: str = ""  # Untuk input NIP
    monthly_data: List[Dict[str, Any]] = []
    MONTH_COLORS = {
        "Jan": "sky",
        "Feb": "blue",
        "Mar": "indigo",
        "Apr": "violet",
        "Mei": "purple",
        "Jun": "plum",
        "Jul": "pink",
        "Aug": "red",
        "Sep": "crimson",
        "Okt": "orange",
        "Nov": "amber",
        "Des": "gold"
    }
    
    @rx.var(cache=True)
    def is_nip_valid(self) -> bool:
        """Check if NIP input is not empty."""
        return bool(self.nip_input.strip())

    @rx.var(cache=True)
    def selected_employee_name(self) -> str:
        """Get name of selected employee."""
        with rx.session() as session:
            employee = session.exec(
                select(Employee).where(Employee.id == self.selected_employee_id)
            ).first()
            return employee.name if employee else ""
        
    def on_mount(self) -> None:
        """Initialize state when component mounts."""
        with rx.session() as session:
            try:
                first_employee = session.exec(
                    select(Employee).order_by(Employee.id.asc()).limit(1)
                ).first()
                
                if first_employee:
                    print(f"Found first employee: {first_employee.name}")
                    self.selected_employee_id = first_employee.id
                    # Explicitly set the selected_deduction to ensure it's initialized
                    self.selected_deduction = "Arisan"
                    # Update monthly_data with fetched data
                    self.monthly_data = self._fetch_monthly_data()
                    print(f"Initial monthly_data: {self.monthly_data}")
                    
            except Exception as e:
                print(f"Error in on_mount: {e}")

    @rx.event
    def search_employee(self):
        """Search employee by NIP."""
        if not self.nip_input:
            return
        
        with rx.session() as session:
            employee = session.exec(
                select(Employee).where(Employee.nip == self.nip_input)
            ).first()
            if employee:
                self.selected_employee_id = employee.id
                self.monthly_data = self._fetch_monthly_data()
                # Clear input after successful search
                self.nip_input = ""
            else:
                return rx.toast.error("Employee not found!", position="bottom-right")

    def _fetch_monthly_data(self) -> List[Dict[str, Any]]:
        """Internal function untuk mengambil data bulanan."""
        if not self.selected_employee_id:
            return []
        
        print(f"Getting data for employee_id: {self.selected_employee_id}")
        print(f"Selected deduction: {self.selected_deduction}")

        with rx.session() as session:
            year = self.current_month.year
            if self.current_page_month == 1:
                start_month, end_month = 1, 6
            else:
                start_month, end_month = 7, 12

            query = text("""
                SELECT 
                    ed.month,
                    SUM(ed.amount) as total_amount
                FROM employee_deductions ed
                JOIN deductions d ON ed.deduction_id = d.id
                WHERE ed.employee_id = :employee_id
                AND d.name = :deduction_name
                AND ed.year = :year
                AND ed.month BETWEEN :start_month AND :end_month
                GROUP BY ed.month
                ORDER BY ed.month
            """)

            result = session.execute(
                query,
                {
                    "employee_id": self.selected_employee_id,
                    "deduction_name": self.selected_deduction,
                    "year": year,
                    "start_month": start_month,
                    "end_month": end_month
                }
            ).fetchall()

            data_dict = {row[0]: row[1] for row in result}
            
            # Perbaiki cara pembuatan data
            formatted_data = []
            for month in range(start_month, end_month + 1):
                month_name = self.month_name(month)
                formatted_data.append({
                    "month": month_name,
                    "amount": data_dict.get(month, 0),
                    "fill": rx.color(self.MONTH_COLORS.get(month_name, "gray"), 9)
                })
            
            return formatted_data

    @rx.event
    def set_selected_deduction(self, value: str):
        """Update selected deduction type."""
        self.selected_deduction = value
        self.monthly_data = self._fetch_monthly_data()
        print(f"Deduction changed to: {value}, data updated")
        
    @rx.event
    def refresh_chart_data(self):
        """Helper event to explicitly refresh chart data."""
        self.monthly_data = self._fetch_monthly_data()
        print("Chart data manually refreshed")

    @rx.var(cache=True)
    def month_page_display(self) -> str:
        """Get current month page display text."""
        year = self.current_month.year
        if self.current_page_month == 1:
            return f"Jan-Jun {year}"
        return f"Jul-Dec {year}"

    @rx.event
    def next_month_page(self):
        """Move to next 6 months."""
        if self.current_page_month == 1:
            self.current_page_month = 2
        else:
            self.current_month = self.current_month.replace(year=self.current_month.year + 1)
            self.current_page_month = 1
        self.monthly_data = self._fetch_monthly_data()

    @rx.event
    def prev_month_page(self):
        """Move to previous 6 months."""
        if self.current_page_month == 2:
            self.current_page_month = 1
        else:
            self.current_month = self.current_month.replace(year=self.current_month.year - 1)
            self.current_page_month = 2
        self.monthly_data = self._fetch_monthly_data()

    def month_name(self, month: int) -> str:
        """Convert month number to abbreviated name."""
        months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", 
                 "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        return months[month - 1]

    # Placeholder functions for download buttons
    @rx.event
    def download_employee_recap(self):
        """Download recap deductions untuk employee yang dipilih."""
        if not self.selected_employee_id:
            return rx.toast.error("No employee selected!", position="bottom-right")

        output = io.StringIO()
        writer = csv.writer(output)
        year = self.current_month.year

        with rx.session() as session:
            # Get employee name
            employee = session.exec(
                select(Employee).where(Employee.id == self.selected_employee_id)
            ).first()

            if not employee:
                return rx.toast.error("Employee not found!", position="bottom-right")

            # Write header
            writer.writerow([f"Recap Deductions Employee by {employee.name} in {year}"])
            writer.writerow([])  # Empty row

            # Write column headers
            headers = ["Deductions"] + ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", 
                                    "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
            writer.writerow(headers)

            # Get data for each deduction type
            deduction_types = ["Arisan", "Iuran DW", "Simpanan Wajib Koperasi", 
                            "Belanja Koperasi", "Simpanan Pokok", "Kredit Khusus", 
                            "Kredit Barang"]

            query = text("""
                SELECT 
                    d.name as deduction_name,
                    ed.month,
                    SUM(ed.amount) as amount
                FROM employee_deductions ed
                JOIN deductions d ON ed.deduction_id = d.id
                WHERE ed.employee_id = :employee_id
                AND ed.year = :year
                GROUP BY d.name, ed.month
                ORDER BY d.name, ed.month
            """)

            result = session.execute(
                query,
                {"employee_id": self.selected_employee_id, "year": year}
            ).fetchall()

            # Convert to dictionary for easier access
            data_dict = {}
            for row in result:
                if row[0] not in data_dict:
                    data_dict[row[0]] = [0] * 12  # Initialize with zeros
                data_dict[row[0]][row[1] - 1] = row[2] or 0

            # Write data rows
            for deduction in deduction_types:
                row_data = [deduction] + [
                    f"{amount:,.0f}".replace(",", ".") if amount else ""
                    for amount in data_dict.get(deduction, [0] * 12)
                ]
                writer.writerow(row_data)

        # Get CSV data and generate filename
        csv_data = output.getvalue()
        output.close()
        filename = f"recap_deductions_{employee.name.replace(' ', '_')}_{year}.csv"

        return rx.download(data=csv_data, filename=filename)

    @rx.event
    def download_all_recap(self):
        """Download recap deductions untuk semua employee."""
        output = io.StringIO()
        writer = csv.writer(output)
        year = self.current_month.year

        with rx.session() as session:
            # Get all employees
            employees = session.exec(select(Employee).order_by(Employee.name)).all()

            for employee in employees:
                # Write header for each employee
                writer.writerow([f"Recap Deductions Employee by {employee.name} in {year}"])
                writer.writerow([])  # Empty row

                # Write column headers
                headers = ["Deductions"] + ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", 
                                        "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
                writer.writerow(headers)

                # Get data for each deduction type
                query = text("""
                    SELECT 
                        d.name as deduction_name,
                        ed.month,
                        SUM(ed.amount) as amount
                    FROM employee_deductions ed
                    JOIN deductions d ON ed.deduction_id = d.id
                    WHERE ed.employee_id = :employee_id
                    AND ed.year = :year
                    GROUP BY d.name, ed.month
                    ORDER BY d.name, ed.month
                """)

                result = session.execute(
                    query,
                    {"employee_id": employee.id, "year": year}
                ).fetchall()

                # Convert to dictionary
                data_dict = {}
                for row in result:
                    if row[0] not in data_dict:
                        data_dict[row[0]] = [0] * 12
                    data_dict[row[0]][row[1] - 1] = row[2] or 0

                # Write data rows
                deduction_types = ["Arisan", "Iuran DW", "Simpanan Wajib Koperasi", 
                                "Belanja Koperasi", "Simpanan Pokok", "Kredit Khusus", 
                                "Kredit Barang"]
                
                for deduction in deduction_types:
                    row_data = [deduction] + [
                        f"{amount:,.0f}".replace(",", ".") if amount else ""
                        for amount in data_dict.get(deduction, [0] * 12)
                    ]
                    writer.writerow(row_data)

                # Add two empty rows between employees
                writer.writerow([])
                writer.writerow([])

        # Get CSV data and generate filename
        csv_data = output.getvalue()
        output.close()
        filename = f"recap_all_deductions_{year}.csv"

        return rx.download(data=csv_data, filename=filename)
    
    @rx.event
    def set_timeframe(self, value: str):
        self.timeframe = value
    
    def get_payment_status_data(self) -> list:
        """Get payment status data."""
        with rx.session() as session:
            current_date = datetime.now()

            if self.timeframe == "Monthly":
                query = """
                    SELECT 
                        COALESCE(payment_status, 'Unknown') as status,
                        COUNT(DISTINCT employee_id) as count
                    FROM employee_deductions
                    WHERE month = :month AND year = :year
                    GROUP BY payment_status
                """
                params = {"month": current_date.month, "year": current_date.year}
            else:  # Yearly
                query = """
                    SELECT 
                        COALESCE(payment_status, 'Unknown') as status,
                        COUNT(DISTINCT employee_id) as count
                    FROM employee_deductions
                    WHERE year = :year
                    GROUP BY payment_status
                """
                params = {"year": current_date.year}

            result = session.execute(text(query), params).fetchall()

            # Mapping warna untuk setiap status pembayaran
            color_mapping = {
                "paid": "var(--jade-8)",        # Warna biru
                "unpaid": "var(--tomato-8)",       # Warna merah
                "installment": "var(--yellow-8)" # Warna ungu
            }

            # Pastikan semua status ada dalam data
            status_counts = {row[0]: row[1] for row in result}
            default_statuses = ["paid", "unpaid", "installment"]

            data = []
            for status in default_statuses:
                count = status_counts.get(status, 0)
                data.append({
                    "name": status.capitalize(),
                    "value": count,
                    "fill": color_mapping.get(status, "var(--gray-8)")  # Default warna abu-abu jika tidak ditemukan
                })

            return data

    @rx.var(cache=True)
    def payment_status_data(self) -> list:
        """Data untuk pie chart payment status."""
        return self.get_payment_status_data()

    
    @rx.var(cache=True)
    def get_deduction_data_last_12_months(self) -> List[Dict[str, Any]]:
        """Mengambil data potongan dari database untuk 12 bulan terakhir."""
        with rx.session() as session:
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            query = text("""
                WITH monthly_totals AS (
                    SELECT 
                        ed.month,
                        ed.year,
                        d.name as deduction_name,
                        SUM(ed.amount) as total_amount
                    FROM employee_deductions ed
                    JOIN deductions d ON ed.deduction_id = d.id
                    WHERE (year = :current_year AND month <= :current_month)
                    OR (year = :previous_year AND month > :current_month)
                    GROUP BY ed.month, ed.year, d.name
                )
                SELECT 
                    month,
                    year,
                    SUM(CASE WHEN deduction_name = 'Arisan' THEN total_amount ELSE 0 END) AS arisan,
                    SUM(CASE WHEN deduction_name = 'Iuran DW' THEN total_amount ELSE 0 END) AS iuran_dw,
                    SUM(CASE WHEN deduction_name = 'Simpanan Wajib Koperasi' THEN total_amount ELSE 0 END) AS simpanan_wajib_koperasi,
                    SUM(CASE WHEN deduction_name = 'Belanja Koperasi' THEN total_amount ELSE 0 END) AS belanja_koperasi,
                    SUM(CASE WHEN deduction_name = 'Simpanan Pokok' THEN total_amount ELSE 0 END) AS simpanan_pokok,
                    SUM(CASE WHEN deduction_name = 'Kredit Khusus' THEN total_amount ELSE 0 END) AS kredit_khusus,
                    SUM(CASE WHEN deduction_name = 'Kredit Barang' THEN total_amount ELSE 0 END) AS kredit_barang
                FROM monthly_totals
                GROUP BY month, year
                ORDER BY year, month
            """)
            
            result = session.execute(query, {
                "current_year": current_year,
                "current_month": current_month,
                "previous_year": current_year - 1
            }).fetchall()

            data = [
                {
                    "month": f"{row[0]}-{row[1]}",
                    "Arisan": row[2],
                    "Iuran DW": row[3],
                    "Simpanan Wajib Koperasi": row[4],
                    "Belanja Koperasi": row[5],
                    "Simpanan Pokok": row[6],
                    "Kredit Khusus": row[7],
                    "Kredit Barang": row[8],
                }
                for row in result
            ]

            return data
        
    def parse_int(self, value):
        """
        Converts the input to an integer.
        
        If input is a string, this function removes any character that is not 
        a digit (e.g., thousand separators or stray letters).
        If the string becomes empty after cleaning, or if value is None,
        the function returns None rather than 0.
        
        Args:
            value (str, int, or None): The input value to convert.
        
        Returns:
            int or None: The converted integer, or None if conversion is not possible.
        """
        # Handle None input: do not convert to 0, return None.
        if value is None:
            return None

        # If the value is a string, remove any non-digit characters
        if isinstance(value, str):
            # Remove any character that is not a digit
            cleaned = re.sub(r'[^\d]', '', value)
            # If the cleaned string is empty, return None
            if cleaned == "":
                return None
        else:
            cleaned = value

        try:
            return int(cleaned)
        except (TypeError, ValueError):
            return None

    async def import_csv(self, files: List[UploadFile]) -> None:
        """Import data dari file CSV dan masukkan ke dalam database."""
        if not files:
            return rx.toast.error("No file uploaded.", position="bottom-right")

        file = files[0]
        content = await file.read()
        print("RAW CSV CONTENT:\n", content.decode('utf-8-sig'))

        df = pd.read_csv(io.StringIO(content.decode('utf-8')), thousands='.')

        print("CSV Columns:", df.columns.tolist())
        print(df.head())

        if 'NIP' not in df.columns:
            return rx.toast.error("CSV file is missing 'NIP' column.", position="bottom-right")

        current_month = self.current_month.month
        current_year = self.current_month.year
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with rx.session() as session:
            for _, row in df.iterrows():
                employee = session.exec(
                    select(Employee).where(Employee.nip == row['NIP'])
                ).first()
                if not employee:
                    employee = Employee(name=row['Nama'], nip=row['NIP'])
                    session.add(employee)
                    session.commit()
                    session.refresh(employee)

                csv_date = row['Date'] if pd.notna(row['Date']) and str(row['Date']).strip() != "" else None

                deductions_values = {
                    "Arisan": self.parse_int(row['Arisan']),
                    "Iuran DW": self.parse_int(row['Iuran DW']),
                    "Simpanan Wajib Koperasi": self.parse_int(row['Simpanan Wajib Koperasi']),
                    "Belanja Koperasi": self.parse_int(row['Belanja Koperasi']),
                    "Simpanan Pokok": self.parse_int(row['Simpanan Pokok']),
                    "Kredit Khusus": self.parse_int(row['Kredit Khusus']),
                    "Kredit Barang": self.parse_int(row['Kredit Barang']),
                }

                for deduction_name, amount in deductions_values.items():
                    ded = session.exec(
                        select(Deduction).where(Deduction.name == deduction_name)
                    ).first()
                    if not ded:
                        continue

                    ed = session.exec(
                        select(EmployeeDeduction).where(
                            EmployeeDeduction.employee_id == employee.id,
                            EmployeeDeduction.deduction_id == ded.id,
                            EmployeeDeduction.month == current_month,
                            EmployeeDeduction.year == current_year
                        )
                    ).first()

                    if ed:
                        if ed.amount != amount or ed.payment_status != row['Status'] or ed.payment_type != row['Type']:
                            ed.amount = amount
                            ed.payment_status = row['Status'] if row['Status'] in ['paid', 'unpaid', 'installment'] else 'unpaid'
                            ed.payment_type = row['Type'] if row['Type'] in ['cash', 'transfer'] else None
                            if csv_date is not None:
                                ed.updated_at = csv_date
                            ed.total_potongan = self.parse_int(row['Total Potongan'])
                            session.add(ed)
                    else:
                        new_date = csv_date if csv_date is not None else ""
                        ed = EmployeeDeduction(
                            employee_id=employee.id,
                            deduction_id=ded.id,
                            amount=amount,
                            payment_status=row['Status'] if row['Status'] in ['paid', 'unpaid', 'installment'] else 'unpaid',
                            payment_type=row['Type'] if row['Type'] in ['cash', 'transfer'] else None,
                            month=current_month,
                            year=current_year,
                            created_at=new_date,
                            updated_at=new_date,
                            total_potongan=self.parse_int(row['Total Potongan']),
                        )
                        session.add(ed)
            session.commit()

        self.load_entries()
        return rx.toast.info("CSV data has been imported successfully.", position="bottom-right")  

    def download_table_data(self) -> None:
        """Generate and download table data as CSV for current month."""
        # Create string buffer
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            'Nama', 'NIP', 'Arisan', 'Iuran DW', 
            'Simpanan Wajib Koperasi', 'Belanja Koperasi', 'Simpanan Pokok', 
            'Kredit Khusus', 'Kredit Barang', 'Total Potongan', 'Date', 'Status', 'Type'
        ]
        writer.writerow(headers)
        
        # Write data rows
        for entry in self.entries:      
            total_potongan = (
                (entry.arisan or 0) +
                (entry.iuran_dw or 0) +
                (entry.simpanan_wajib_koperasi or 0) +
                (entry.belanja_koperasi or 0) +
                (entry.simpanan_pokok or 0) +
                (entry.kredit_khusus or 0) +
                (entry.kredit_barang or 0)
            )
            total_potongan = total_potongan if total_potongan != 0 else ''
            row = [
                entry.name,
                entry.nip,
                entry.arisan or '',
                entry.iuran_dw or '',
                entry.simpanan_wajib_koperasi or '',
                entry.belanja_koperasi or '',
                entry.simpanan_pokok or '',
                entry.kredit_khusus or '',
                entry.kredit_barang or '',
                total_potongan,
                entry.date,
                entry.status,
                entry.payment_type
            ]
            writer.writerow(row)
        
        # Get the CSV data
        csv_data = output.getvalue()
        output.close()
        
        # Generate filename with current month and year
        filename = f"employee_deductions_{self.current_month.strftime('%B_%Y')}.csv"
        
        return rx.download(
            data=csv_data,
            filename=filename,
        )

    def download_all_deduction_slips(self):
        """Generate and download deduction slips for all employees."""
        # Create string buffer
        output = io.StringIO()
        writer = csv.writer(output)
        
        month_name = calendar.month_name[self.current_month.month]
        year = self.current_month.year
        
        for entry in self.entries:
            # Write title
            writer.writerow([])  # Empty row for spacing
            writer.writerow([f'DAFTAR POTONGAN KOPERASI DAN LAIN-LAIN BULAN {month_name.upper()} {year}'])
            writer.writerow([])
            
            # Write employee info
            writer.writerow([f'Nama         :', entry.name])
            writer.writerow([f'Potongan   :'])
            
            # Define deductions and write them
            total_amount = 0
            deductions = [
                ('Arisan', entry.arisan),
                ('Iuran DW', entry.iuran_dw),
                ('Simpanan Wajib Koperasi', entry.simpanan_wajib_koperasi),
                ('Belanja Koperasi', entry.belanja_koperasi),
                ('Simpanan Pokok', entry.simpanan_pokok),
                ('Kredit Khusus', entry.kredit_khusus),
                ('Kredit Barang', entry.kredit_barang),
            ]
            
            # Write deductions that have values
            for deduction_name, amount in deductions:
                writer.writerow(['', deduction_name, f'{amount:,.0f}'.replace(',', '.')] if amount else ['', deduction_name, ''])
                if amount:
                    total_amount += amount
            
            writer.writerow(['', 'Total Potongan', f'{total_amount:,.0f}'.replace(',', '.')])
            writer.writerow([])  # Empty row for spacing
        
        # Get the CSV data
        csv_data = output.getvalue()
        output.close()
        
        # Generate filename
        filename = f"all_deduction_slips_{month_name}_{year}.csv"
        
        return rx.download(
            data=csv_data,
            filename=filename,
        )

    def download_deduction_slip(self, entry: EmployeeDeductionEntry):
        """Generate and download deduction slip for an employee."""
        # Create string buffer
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write title
        month_name = calendar.month_name[self.current_month.month]
        year = self.current_month.year
        writer.writerow([])  # Empty row for spacing
        writer.writerow([f'DAFTAR POTONGAN KOPERASI DAN LAIN-LAIN BULAN {month_name.upper()} {year}'])
        writer.writerow([])
        
        # Write employee info
        writer.writerow([f'Nama         :', entry.name])
        writer.writerow([f'Potongan   :'])
        
        # Define deductions and write them
        total_amount = 0
        deductions = [
            ('Arisan', entry.arisan),
            ('Iuran DW', entry.iuran_dw),
            ('Simpanan Wajib Koperasi', entry.simpanan_wajib_koperasi),
            ('Belanja Koperasi', entry.belanja_koperasi),
            ('Simpanan Pokok', entry.simpanan_pokok),
            ('Kredit Khusus', entry.kredit_khusus),
            ('Kredit Barang', entry.kredit_barang),
        ]
        
        # Write deductions that have values
        for deduction_name, amount in deductions:
            writer.writerow(['', deduction_name, f'{amount:,.0f}'.replace(',', '.')] if amount else ['', deduction_name, ''])
            if amount:
                total_amount += amount
        
        writer.writerow(['', 'Total Potongan', f'{total_amount:,.0f}'.replace(',', '.')])
        writer.writerow([]) 
        
        # Get the CSV data
        csv_data = output.getvalue()
        output.close()
        
        # Generate filename
        filename = f"deduction_slip_{entry.name.replace(' ', '_')}_{month_name}_{year}.csv"
        
        return rx.download(
            data=csv_data,
            filename=filename,
        )
    
    def next_month(self):
        """Pindah ke bulan berikutnya."""
        self.current_month = (self.current_month.replace(day=1) + timedelta(days=32)).replace(day=1)
        self.load_entries()

    def prev_month(self):
        """Pindah ke bulan sebelumnya."""
        self.current_month = (self.current_month.replace(day=1) - timedelta(days=1)).replace(day=1)
        self.load_entries()    
        
    @rx.var(cache=True)
    def formatted_month(self) -> str:
        """Format bulan untuk ditampilkan."""
        return self.current_month.strftime("%B %Y")


    def handle_input_change(self, value: str, field_name: str):
        """Handle perubahan nilai input."""
        if hasattr(self.current_entry, field_name):
            setattr(self.current_entry, field_name, value)
            
    def load_entries(self) -> None:
        with rx.session() as session:
            query = """
                SELECT 
                    e.id,
                    e.name,
                    e.nip,
                    MAX(CASE WHEN d.name = 'Arisan' THEN ed.amount END) AS arisan,
                    MAX(CASE WHEN d.name = 'Iuran DW' THEN ed.amount END) AS iuran_dw,
                    MAX(CASE WHEN d.name = 'Simpanan Wajib Koperasi' THEN ed.amount END) AS simpanan_wajib_koperasi,
                    MAX(CASE WHEN d.name = 'Belanja Koperasi' THEN ed.amount END) AS belanja_koperasi,
                    MAX(CASE WHEN d.name = 'Simpanan Pokok' THEN ed.amount END) AS simpanan_pokok,
                    MAX(CASE WHEN d.name = 'Kredit Khusus' THEN ed.amount END) AS kredit_khusus,
                    MAX(CASE WHEN d.name = 'Kredit Barang' THEN ed.amount END) AS kredit_barang,
                    MAX(ed.updated_at) AS date,
                    MAX(ed.payment_status) AS status,
                    MAX(ed.payment_type) AS payment_type
                FROM employees e
                LEFT JOIN employee_deductions ed ON ed.employee_id = e.id 
                    AND ed.month = :month 
                    AND ed.year = :year
                LEFT JOIN deductions d ON ed.deduction_id = d.id
                GROUP BY e.id, e.name, e.nip
            """
            
            try:
                result = session.execute(
                    text(query), 
                    {
                        "month": self.current_month.month,
                        "year": self.current_month.year
                    }
                )
                entries = []
                for row in result:
                    try:
                        total_potongan = (
                            (row[3] or 0) +
                            (row[4] or 0) +
                            (row[5] or 0) +
                            (row[6] or 0) +
                            (row[7] or 0) +
                            (row[8] or 0) +
                            (row[9] or 0)
                        )
                        total_potongan = total_potongan if total_potongan != 0 else None
                        row_dict = {
                            "id": row[0],
                            "name": row[1],
                            "nip": row[2],
                            "arisan": row[3] if row[3] is not None else None,
                            "iuran_dw": row[4] if row[4] is not None else None,
                            "simpanan_wajib_koperasi": row[5] if row[5] is not None else None,
                            "belanja_koperasi": row[6] if row[6] is not None else None,
                            "simpanan_pokok": row[7] if row[7] is not None else None,
                            "kredit_khusus": row[8] if row[8] is not None else None,
                            "kredit_barang": row[9] if row[9] is not None else None,
                            "total_potongan": total_potongan,
                            "date": str(row[10] or ""),
                            "status": str(row[11] or ""),
                            "payment_type": str(row[12] or "")
                        }
                        entry = EmployeeDeductionEntry(**row_dict)
                        entries.append(entry)
                    except Exception as e:
                        print(f"Error creating entry object: {e}")
                        continue

                # Terapkan pencarian jika ada
                if self.search_value:
                    search_lower = self.search_value.lower()
                    entries = [
                        r for r in entries
                        if search_lower in r.name.lower() or search_lower in r.nip.lower()
                    ]

                # Terapkan sorting jika ada
                if self.sort_value:
                    entries.sort(
                        key=lambda r: getattr(r, self.sort_value) or "",
                        reverse=self.sort_reverse
                    )

                self.entries = entries
                print(f"Successfully loaded {len(entries)} entries")
                
            except Exception as e:
                print(f"Error in load_entries: {e}")
                self.entries = []

            # Update nilai agregat
            self.get_current_month_values()
            self.get_previous_month_values()
     
    def get_current_month_values(self):
        """Contoh perhitungan agregat untuk bulan ini."""
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        # Asumsikan kolom 'date' dalam format "%Y-%m-%d %H:%M:%S"
        current_entries = [
            entry for entry in self.entries
            if entry.date and datetime.strptime(entry.date, "%Y-%m-%d %H:%M:%S") >= start_of_month
        ]
        num_entries = len(current_entries)
        total = sum(
            (entry.arisan or 0) +
            (entry.iuran_dw or 0) +
            (entry.simpanan_wajib_koperasi or 0) +
            (entry.belanja_koperasi or 0) +
            (entry.simpanan_pokok or 0) +
            (entry.kredit_khusus or 0) +
            (entry.kredit_barang or 0)
            for entry in current_entries
        )
        self.current_month_values = MonthValues(num_entries=num_entries, total_payments=total)

    def get_previous_month_values(self):
        """Contoh perhitungan agregat untuk bulan sebelumnya."""
        now = datetime.now()
        first_day_of_current_month = datetime(now.year, now.month, 1)
        last_day_previous = first_day_of_current_month - timedelta(days=1)
        start_of_previous = datetime(last_day_previous.year, last_day_previous.month, 1)
        previous_entries = [
            entry for entry in self.entries
            if entry.date and start_of_previous <= datetime.strptime(entry.date, "%Y-%m-%d %H:%M:%S") <= last_day_previous
        ]
        num_entries = len(previous_entries)
        total = sum(
            (entry.arisan or 0) +
            (entry.iuran_dw or 0) +
            (entry.simpanan_wajib_koperasi or 0) +
            (entry.belanja_koperasi or 0) +
            (entry.simpanan_pokok or 0) +
            (entry.kredit_khusus or 0) +
            (entry.kredit_barang or 0)
            for entry in previous_entries
        )
        self.previous_month_values = MonthValues(num_entries=num_entries, total_payments=total)
                
    def sort_values(self, sort_value: str):
        self.sort_value = sort_value
        self.load_entries()

    def toggle_sort(self):
        self.sort_reverse = not self.sort_reverse
        self.load_entries()

    def filter_values(self, search_value: str):
        self.search_value = search_value
        self.load_entries()

    def get_entry(self, entry: EmployeeDeductionEntry):
        print("Current entry:", entry.__dict__) 
        self.current_entry = entry

    def add_employee_entry(self, form_data: dict):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_month = self.current_month.month
        current_year = self.current_month.year
        with rx.session() as session:
            # Buat record pegawai baru
            employee = Employee(name=form_data.get("name"), nip=form_data.get("nip"))
            session.add(employee)
            session.commit()
            session.refresh(employee)
            employee_name = employee.name
            
            # Daftar deduction dan nilai dari form_data
            deductions_values = {
                "Arisan": int(form_data.get("arisan")) if form_data.get("arisan") else None,
                "Iuran DW": int(form_data.get("iuran_dw")) if form_data.get("iuran_dw") else None,
                "Simpanan Wajib Koperasi": int(form_data.get("simpanan_wajib_koperasi")) if form_data.get("simpanan_wajib_koperasi") else None,
                "Belanja Koperasi": int(form_data.get("belanja_koperasi")) if form_data.get("belanja_koperasi") else None,
                "Simpanan Pokok": int(form_data.get("simpanan_pokok")) if form_data.get("simpanan_pokok") else None,
                "Kredit Khusus": int(form_data.get("kredit_khusus")) if form_data.get("kredit_khusus") else None,
                "Kredit Barang": int(form_data.get("kredit_barang")) if form_data.get("kredit_barang") else None,
            }
            for deduction_name, amount in deductions_values.items():
                # Dapatkan record deduction berdasarkan nama
                ded = session.exec(
                    select(Deduction).where(Deduction.name == deduction_name)
                ).first()
                if not ded:
                    continue  # atau bisa tambahkan log/error jika record tidak ditemukan
                ed = EmployeeDeduction(
                    employee_id=employee.id,
                    deduction_id=ded.id,
                    amount = int(amount) if amount else None,
                    payment_status=form_data.get("status"),
                    payment_type=form_data.get("payment_type"),
                    month=current_month,
                    year=current_year,
                    created_at=now_str,
                    updated_at=now_str,
                )
                session.add(ed)
            session.commit()
        self.load_entries()
        return rx.toast.info(f"Entry for {employee_name} has been added for {self.formatted_month}.", position="bottom-right")

    def update_employee_entry(self, form_data: dict):
        """
        Memperbarui data entry yang sudah ada.
        form_data diharapkan memiliki kunci:
        name, nip, arisan, denda_arisan, iuran_dw, simpanan_wajib_koperasi,
        belanja_koperasi, simpanan_pokok, kredit_khusus, kredit_barang, status, payment_type
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_month = self.current_month.month
        current_year = self.current_month.year
        with rx.session() as session:
            # Perbarui data pegawai
            employee = session.exec(
                select(Employee).where(Employee.id == self.current_entry.id)
            ).first()
            employee.name = form_data.get("name")
            employee.nip = form_data.get("nip")
            session.add(employee)
            session.commit()
            employee_name = str(employee.name)

            # Perbarui tiap record potongan untuk periode (bulan & tahun) saat ini
            deductions_values = {
            "Arisan": int(form_data.get("arisan")) if form_data.get("arisan") else None,
            "Iuran DW": int(form_data.get("iuran_dw")) if form_data.get("iuran_dw") else None,
            "Simpanan Wajib Koperasi": int(form_data.get("simpanan_wajib_koperasi")) if form_data.get("simpanan_wajib_koperasi") else None,
            "Belanja Koperasi": int(form_data.get("belanja_koperasi")) if form_data.get("belanja_koperasi") else None,
            "Simpanan Pokok": int(form_data.get("simpanan_pokok")) if form_data.get("simpanan_pokok") else None,
            "Kredit Khusus": int(form_data.get("kredit_khusus")) if form_data.get("kredit_khusus") else None,
            "Kredit Barang": int(form_data.get("kredit_barang")) if form_data.get("kredit_barang") else None,
            }
            for deduction_name, amount in deductions_values.items():
                ded = session.exec(
                    select(Deduction).where(Deduction.name == deduction_name)
                ).first()
                if not ded:
                    continue
                # Cari record EmployeeDeduction untuk pegawai ini, deduction ini, dan periode saat ini
                ed = session.exec(
                    select(EmployeeDeduction).where(
                        EmployeeDeduction.employee_id == employee.id,
                        EmployeeDeduction.deduction_id == ded.id,
                        EmployeeDeduction.month == current_month,
                        EmployeeDeduction.year == current_year
                    )
                ).first()
                if ed:
                    ed.amount = amount
                    ed.payment_status = form_data.get("status")
                    ed.payment_type = form_data.get("payment_type")
                    ed.updated_at = now_str
                    session.add(ed)
                else:
                    new_ed = EmployeeDeduction(
                        employee_id=employee.id,
                        deduction_id=ded.id,
                        amount=amount ,
                        payment_status=form_data.get("status"),
                        payment_type=form_data.get("payment_type"),
                        month=current_month,
                        year=current_year,
                        created_at=now_str,
                        updated_at=now_str,
                    )
                    session.add(new_ed)
            session.commit()
        self.load_entries()
        return rx.toast.info(f"Entry for {employee_name} has been updated for {self.formatted_month}.", position="bottom-right")

    def delete_employee(self, id: int):
        """Menghapus entry pegawai (cascade akan menghapus data potongan terkait)."""
        with rx.session() as session:
            employee = session.exec(select(Employee).where(Employee.id == id)).first()
            session.delete(employee)
            session.commit()
        self.load_entries()
        return rx.toast.info(f"Entry for {employee.name} has been deleted.", position="bottom-right")

    # Contoh perhitungan persentase perubahan (bisa disesuaikan jika diperlukan)
    def _get_percentage_change(self, value: Union[int, int], prev_value: Union[int, int]) -> int:
        if prev_value == 0:
            return 10000
        return round(((value - prev_value) / prev_value) * 100, 2)

    @rx.var(cache=True)
    def payments_change(self) -> int:
        return self._get_percentage_change(
            self.current_month_values.total_payments,
            self.previous_month_values.total_payments,
        )


    @rx.var(cache=True)
    def entries_change(self) -> int:
        return self._get_percentage_change(
            self.current_month_values.num_entries,
            self.previous_month_values.num_entries,
        )
        
    @rx.var(cache=True)
    def page_number(self) -> int:
        """Mendapatkan nomor halaman saat ini."""
        return (self.offset // self.limit) + 1

    @rx.var(cache=True)
    def total_pages(self) -> int:
        """Mendapatkan total jumlah halaman."""
        return (len(self.entries) // self.limit) + (1 if len(self.entries) % self.limit else 0)

    @rx.var(cache=True)
    def current_page_entries(self) -> List[EmployeeDeductionEntry]:
        """Mendapatkan entries untuk halaman saat ini."""
        start = self.offset
        end = start + self.limit
        return self.entries[start:end]

    def prev_page(self):
        """Pindah ke halaman sebelumnya."""
        if self.page_number > 1:
            self.offset -= self.limit

    def next_page(self):
        """Pindah ke halaman berikutnya."""
        if self.page_number < self.total_pages:
            self.offset += self.limit

    def first_page(self):
        """Pindah ke halaman pertama."""
        self.offset = 0

    def last_page(self):
        """Pindah ke halaman terakhir."""
        self.offset = (self.total_pages - 1) * self.limit
        
    @rx.event
    def reset_table_filters(self):
        """Reset all table filters to default state."""
        self.search_value = ""
        self.sort_value = ""
        self.sort_reverse = False
        self.offset = 0  # Reset pagination juga
        self.load_entries()