import React from 'react';
import '../css/UploadButton.css';

const UploadButton = () => {
  return (
    <div className="upload-container">
      <h2 className="subheading">Welcome to Flashbook</h2> {/* Subheading above the upload button */}
      <label htmlFor="file-upload" className="upload-icon">
        Upload
      </label>
      <input id="file-upload" type="file" className="upload-input" />
    </div>
  );
};

export default UploadButton;
