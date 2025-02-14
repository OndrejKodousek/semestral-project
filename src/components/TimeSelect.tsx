import React from "react";

interface TimeSelectProps {
  setTime: (time: string) => void;
}

const TimeSelect: React.FC<TimeSelectProps> = ({ setTime }) => {
  return (
    <div className="inset-container p-3 h-100">
      <h3 className="mb-3 no-select">Choose Time</h3>
      <div className="pb-2 no-select">
        <input
          type="radio"
          id="control_01"
          name="select"
          value="1"
          onChange={(e) => setTime(e.target.value)}
        />
        <label htmlFor="control_01" className="radio-container">
          <div className="p-2 bold-text">1 Day</div>
        </label>
      </div>

      <div className="pb-2 no-select">
        <input
          type="radio"
          id="control_02"
          name="select"
          value="3"
          onChange={(e) => setTime(e.target.value)}
        />
        <label htmlFor="control_02" className="radio-container">
          <div className="p-2 bold-text">3 Days</div>
        </label>
      </div>

      <div className="pb-2 no-select">
        <input
          type="radio"
          id="control_03"
          name="select"
          value="7"
          onChange={(e) => setTime(e.target.value)}
        />
        <label htmlFor="control_03" className="radio-container">
          <div className="p-2 bold-text">7 Days</div>
        </label>
      </div>
    </div>
  );
};

export default TimeSelect;
