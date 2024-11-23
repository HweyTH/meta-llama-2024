import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../css/CourseTabs.css';

const CourseTabs = ({ courses }) => {
  const navigate = useNavigate();

  if (!courses || courses.length === 0) {
    return <p>No courses available.</p>;
  }

  return (
    <div className="course-tabs-container">
      {courses.map((course, index) => (
        <div
          key={index}
          className="course-tab"
          onClick={() => navigate(`/course/${index}`)}
          role="button"
          aria-label={`Navigate to ${course.name}`}
          tabIndex={0}
        >
          {course.name}
        </div>
      ))}
    </div>
  );
};

export default CourseTabs;
