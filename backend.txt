import io
import csv
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import calendar
from typing import Union, List
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
    
    async def import_csv(self, files: List[UploadFile]) -> None:
        """Import data from CSV file and insert into the database."""
        if not files:
            return rx.toast.error("No file uploaded.", position="bottom-right")

        file = files[0]
        content = await file.read()
        print("RAW CSV CONTENT:\n", content.decode('utf-8-sig'))

        # Gunakan pandas untuk membaca CSV
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))

        # Cetak nama kolom untuk debugging
        print("CSV Columns:", df.columns.tolist())
        print(df.head())

        # Pastikan kolom 'NIP' ada dalam data CSV
        if 'NIP' not in df.columns:
            return rx.toast.error("CSV file is missing 'NIP' column.", position="bottom-right")

        current_month = self.current_month.month
        current_year = self.current_month.year
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with rx.session() as session:
            for _, row in df.iterrows():
                # Buat record pegawai baru atau dapatkan yang sudah ada
                employee = session.exec(
                    select(Employee).where(Employee.nip == row['NIP'])
                ).first()
                if not employee:
                    employee = Employee(name=row['Nama'], nip=row['NIP'])
                    session.add(employee)
                    session.commit()
                    session.refresh(employee)

                # Parse CSV date (jika ada); jika kosong, jadikan None
                csv_date = row['Date'] if pd.notna(row['Date']) and str(row['Date']).strip() != "" else None

                # Daftar deduction dan nilai dari CSV
                deductions_values = {
                    "Arisan": int(row['Arisan']) if pd.notna(row['Arisan']) else None,
                    "Iuran DW": int(row['Iuran DW']) if pd.notna(row['Iuran DW']) else None,
                    "Simpanan Wajib Koperasi": int(row['Simpanan Wajib Koperasi']) if pd.notna(row['Simpanan Wajib Koperasi']) else None,
                    "Belanja Koperasi": int(row['Belanja Koperasi']) if pd.notna(row['Belanja Koperasi']) else None,
                    "Simpanan Pokok": int(row['Simpanan Pokok']) if pd.notna(row['Simpanan Pokok']) else None,
                    "Kredit Khusus": int(row['Kredit Khusus']) if pd.notna(row['Kredit Khusus']) else None,
                    "Kredit Barang": int(row['Kredit Barang']) if pd.notna(row['Kredit Barang']) else None,
                }
                for deduction_name, amount in deductions_values.items():
                    ded = session.exec(
                        select(Deduction).where(Deduction.name == deduction_name)
                    ).first()
                    if not ded:
                        continue

                    # Periksa apakah ada entri yang sudah ada untuk pegawai ini, deduction ini, dan periode saat ini
                    ed = session.exec(
                        select(EmployeeDeduction).where(
                            EmployeeDeduction.employee_id == employee.id,
                            EmployeeDeduction.deduction_id == ded.id,
                            EmployeeDeduction.month == current_month,
                            EmployeeDeduction.year == current_year
                        )
                    ).first()

                    if ed:
                        # Jika entri sudah ada, update hanya jika ada perubahan
                        if ed.amount != amount or ed.payment_status != row['Status'] or ed.payment_type != row['Type']:
                            ed.amount = amount
                            ed.payment_status = row['Status'] if row['Status'] in ['paid', 'unpaid', 'installment'] else 'unpaid'
                            ed.payment_type = row['Type'] if row['Type'] in ['cash', 'transfer'] else None
                            # Jika CSV date tersedia, gunakan CSV date; jika kosong, jangan mengubah updated_at
                            if csv_date is not None:
                                ed.updated_at = csv_date
                            ed.total_potongan = int(row['Total Potongan']) if pd.notna(row['Total Potongan']) else None
                            session.add(ed)
                    else:
                        # Untuk entri baru, gunakan CSV date jika ada; kalau tidak, set sebagai kosong ("")
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
                            total_potongan=int(row['Total Potongan']) if pd.notna(row['Total Potongan']) else None,
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
    
    def download_deduction_slip(self, entry: EmployeeDeductionEntry):
        """Generate and download deduction slip for an employee."""
        # Create string buffer
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write title
        month_name = calendar.month_name[self.current_month.month]
        year = self.current_month.year
        writer.writerow([f'LIST OF COOPERATIVE DEDUCTIONS FOR THE MONTH OF {month_name} {year}'])
        writer.writerow([])  # Empty row for spacing
        
        # Write employee info
        writer.writerow(['Name', ':', entry.name])
        writer.writerow([])  # Empty row for spacing
        
        # Write deductions header
        writer.writerow(['Deductions:'])
        
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
            if amount:  # Only write if amount exists
                writer.writerow(['', deduction_name, f'Rp {amount:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')])
                total_amount += amount
        
        writer.writerow([])  # Empty row for spacing
        writer.writerow(['', 'Jumlah Potongan', f'Rp {total_amount:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')])
        
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