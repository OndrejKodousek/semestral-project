import React from "react";

interface UpdateButtonProps {
  ticker: string | null;
  model: string | null;
  time: string | null;
  setData: (data: any) => void;
}

const UpdateButton: React.FC<UpdateButtonProps> = ({
  ticker,
  model,
  time,
  setData,
}) => {
  const fetchResults = async () => {
    if (!ticker || !model || !time) {
      alert("Please select all options before fetching results.");
      return;
    }

    try {
      const response = await fetch("https://kodousek.cz/api/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        mode: "cors",
        body: JSON.stringify({ ticker, model, time }),
      });

      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error("Error fetching results:", error);
    }
  };

  return (
    <div className="mb-3 d-flex justify-content-center align-items-center">
      <button className="btn btn-primary" onClick={fetchResults}>
        Fetch Results
      </button>
    </div>
  );
};

export default UpdateButton;
