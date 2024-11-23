import React from 'react';
import { useParams } from 'react-router-dom';
import '../css/CourseSummary.css';

const CourseSummary = ({ courses }) => {
  const { id } = useParams();
  const course = courses ? courses[id] : null;

  const handleAudioGeneration = () => {
    console.log('Generating audio...');
    alert('Audio file generation is in progress!');
  };

  if (!course) {
    return <p>Course not found!</p>;
  }

  return (
    <div className="course-summary-container">
      <h2>{course.name} Summary</h2>
      <p>{course.summary || 'No summary available.'}</p>
      <button onClick={handleAudioGeneration} className="generate-audio-button">
        Generate Audio File
      </button>
    </div>
  );
};

export default CourseSummary;
