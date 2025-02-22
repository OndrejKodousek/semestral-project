const formatDate = (date: Date): string => {
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  return `${day}-${month}`;
  //const year = date.getFullYear();
  //return `${day}-${month}-${year}`;
};

export const generateWeekDates = (startDate: string): string[] => {
  const date = new Date(startDate);
  const weekDates = [formatDate(date)];
  for (let i = 1; i < 7; i++) {
    const nextDate = new Date(date);
    nextDate.setDate(date.getDate() + i);
    weekDates.push(formatDate(nextDate));
  }

  return weekDates;
};

export const getCurrentDate = () => {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0"); // Months are 0-indexed
  const day = String(today.getDate()).padStart(2, "0");
  return `${day}-${month}`;
};
