import React from 'react';

const KeyboardCommands: React.FC = () => {
  return (
    <div className="keyboard-commands">
      <h2>Keyboard Commands</h2>
      <ul>
        <li>ArrowDown: Speed up drop</li>
        <li>ArrowUp: Rotate block</li>
        <li>ArrowLeft: Move left</li>
        <li>ArrowRight: Move right</li>
      </ul>
    </div>
  );
};

export default KeyboardCommands;
