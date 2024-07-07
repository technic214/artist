function parseISOString(isoString) {
  const dateParts = isoString.split(/\D+/).map(Number);
  const [year, month, day, hour, minute, second, millisecond] = dateParts;

  return new Date(Date.UTC(year, month - 1, day, hour, minute, second, millisecond));
}
