function onEdit(e) {
    var sheet = e.source.getActiveSheet();
    var range = e.range;
    var editedColumn = range.getColumn();
    var editedRow = range.getRow();
    
    // Kolom yang ingin dipantau (Arisan sampai Kredit Barang)
    var watchColumns = [3, 4, 5, 6, 7, 8, 9]; 
    
    // Kolom untuk timestamp (Date)
    var timestampColumn = 11; 
    
    // Kolom untuk Total Potongan
    var totalPotonganColumn = 10; 
  
    // Jika edit terjadi di kolom yang dipantau, update timestamp & total potongan
    if (watchColumns.includes(editedColumn)) {
      var timestamp = new Date();
      var formattedTimestamp = Utilities.formatDate(timestamp, Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm:ss");
  
      // Hitung total potongan
      var totalPotongan = 0;
      for (var i = 0; i < watchColumns.length; i++) {
        totalPotongan += Number(sheet.getRange(editedRow, watchColumns[i]).getValue()) || 0; 
      }
  
      // Simpan hasil ke Google Sheets
      sheet.getRange(editedRow, timestampColumn).setValue(formattedTimestamp);
      sheet.getRange(editedRow, totalPotonganColumn).setValue(totalPotongan);
      
      // Format angka untuk semua kolom uang termasuk Total Potongan
      var moneyColumns = [...watchColumns, totalPotonganColumn]; 
      moneyColumns.forEach(col => {
        sheet.getRange(editedRow, col).setNumberFormat("#,###"); 
      });
    }
  }
  