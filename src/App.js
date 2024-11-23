import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import UploadButton from './components/UploadButton';
import CourseTabs from './components/CourseTabs';
import CourseSummary from './components/CourseSummary';

const App = () => {
  const [courses, setCourses] = useState([]);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const newCourse = {
        name: file.name,
        summary: `Summary for ${file.name}`, // Placeholder
      };
      setCourses([...courses, newCourse]);
    }
  };

  return (
    <Router>
      <div>
        <Navbar />
        <Routes>
          <Route
            path="/"
            element={
              <>
                <UploadButton handleFileUpload={handleFileUpload} />
                <CourseTabs courses={courses} />
              </>
            }
          />
          <Route
            path="/course/:id"
            element={<CourseSummary courses={courses} />}
          />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
