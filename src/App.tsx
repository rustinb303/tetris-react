import Board from './components/Board';
import UpcomingBlocks from './components/UpcomingBlocks';
import HighScores from './components/HighScores';
import { useTetris } from './hooks/useTetris';

function App() {
  const { board, startGame, isPlaying, score, upcomingBlocks, isHardcoreMode, toggleHardcoreMode } = useTetris();

  return (
    <div className="app">
      <h1>Tetris</h1>
      <Board currentBoard={board} />
      <div className="controls">
        <h2>Score: {score}</h2>
        <div className="mode-controls">
          <label>
            <input
              type="checkbox"
              checked={isHardcoreMode}
              onChange={toggleHardcoreMode}
              disabled={isPlaying}
            />
            Hardcore Mode (10x faster)
          </label>
          {isHardcoreMode && <p className="mode-indicator">🔥 HARDCORE MODE ACTIVE 🔥</p>}
        </div>
        {isPlaying ? (
          <UpcomingBlocks upcomingBlocks={upcomingBlocks} />
        ) : (
          <>
            <button onClick={startGame}>New Game</button>
            <HighScores />
          </>
        )}
      </div>
    </div>
  );
}

export default App;
