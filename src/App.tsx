import Board from './components/Board';
import UpcomingBlocks from './components/UpcomingBlocks';
import HighScores from './components/HighScores';
import { useTetris } from './hooks/useTetris';

function App() {
  const { board, startGame, startHardcoreGame, isPlaying, score, upcomingBlocks } = useTetris();

  return (
    <div className="app">
      <h1>Tetris</h1>
      <Board currentBoard={board} />
      <div className="controls">
        <h2>Score: {score}</h2>
        {isPlaying ? (
          <UpcomingBlocks upcomingBlocks={upcomingBlocks} />
        ) : (
          <>
            <button onClick={startGame}>New Game</button>
            <button onClick={startHardcoreGame}>Hardcore Mode</button>
            <HighScores />
          </>
        )}
      </div>
    </div>
  );
}

export default App;
