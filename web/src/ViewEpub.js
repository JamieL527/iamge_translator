import React, { useState, useEffect } from "react";
import { ReactReader } from "react-reader";

const ViewEpub = ({ translatedFilePath }) => {
  const [location, setLocation] = useState(null);

  useEffect(() => {
    
  }, []);

  const handleLocationChanged = (newLocation) => {
    setLocation(newLocation); 
  };

  return (
    <div style={{ height: "80vh" }}>
      <ReactReader
        url={`http://localhost:5001/api/view-epub/${translatedFilePath}`}
        title="Translated EPUB"
        location={location}
        locationChanged={handleLocationChanged}
      />
    </div>
  );
};

export default ViewEpub;



