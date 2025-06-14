import React from 'react';
// Import the updated camel-cased helper
import { getHighScores } from '../hooks/useTetris';

function HighScores() {
  // Fetch top scores (already sorted in helper) and limit to 10 entries
  const highScores = getHighScores().slice(0, 10);
  
  if (highScores.length === 0) {
    return (
      <div className="high-scores">
        <h2>High Scores</h2>
        <p>No high scores yet!</p>
      </div>
    );
  }

  return (
    <div className="high-scores">
      <h2>High Scores</h2>
      <ol className="high-scores-list">
        {highScores.map((score: number, index: number) => (
          <li key={index} className="high-score-item">
            {score}
          </li>
        ))}
      </ol>
    </div>
  );
}

export default HighScores;
