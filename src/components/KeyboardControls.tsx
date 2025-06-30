interface KeyboardControlsProps {
  className?: string;
}

function KeyboardControls({ className }: KeyboardControlsProps) {
  return (
    <div className={`keyboard-controls ${className || ''}`}>
      <h3>Controls</h3>
      <div className="controls-list">
        <div className="control-item">
          <div className="key-icon">←</div>
          <span>Move Left</span>
        </div>
        <div className="control-item">
          <div className="key-icon">→</div>
          <span>Move Right</span>
        </div>
        <div className="control-item">
          <div className="key-icon">↑</div>
          <span>Rotate</span>
        </div>
        <div className="control-item">
          <div className="key-icon">↓</div>
          <span>Fast Drop</span>
        </div>
      </div>
    </div>
  );
}

export default KeyboardControls;