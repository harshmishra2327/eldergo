function getKolkataDateString() {
    return new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' });
}

function getKolkataTimeString() {
    return new Date().toLocaleTimeString('en-GB', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' });
}

function isFutureKolkataDateTime(dateStr, timeStr) {
    if (!dateStr || !timeStr) return false;
    const timeFormatted = timeStr.length === 5 ? timeStr + ':00' : timeStr;
    const isoStr = `${dateStr}T${timeFormatted}+05:30`;
    const selectedMs = new Date(isoStr).getTime();
    return !isNaN(selectedMs) && selectedMs > Date.now();
}

console.log('Today Kolkata Date:', getKolkataDateString());
console.log('Today Kolkata Time:', getKolkataTimeString());

const today = getKolkataDateString();
console.log('Past time today:', isFutureKolkataDateTime(today, '08:00'));
console.log('Future time today (23:59):', isFutureKolkataDateTime(today, '23:59'));
console.log('Past date:', isFutureKolkataDateTime('2025-01-01', '10:00'));
console.log('Future date:', isFutureKolkataDateTime('2030-01-01', '10:00'));
