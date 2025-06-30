/**
 * useTetris.ts
 * 
 * Main Tetris game logic hook that manages game state, user input, scoring,
 * and game loop timing. Provides the primary interface for the Tetris game
 * including starting games, handling player movements, and managing high scores.
 */

import { useCallback, useEffect, useState } from 'react';
import { Block, BlockShape, BoardShape, EmptyCell, SHAPES } from '../types';
import { useInterval } from './useInterval';
import { useTetrisBoard, hasCollisions, BOARD_HEIGHT, getEmptyBoard, getRandomBlock } from './useTetrisBoard';

// Maximum number of high scores to store
const MAX_HIGH_SCORES = 10;

/**
 * Saves a new high score to localStorage.
 * Maintains a sorted list of the top scores, keeping only the highest scores
 * up to the maximum limit.
 * 
 * @param score - The score to save
 */
export function saveHighScore(score: number): void {
  const existingScores = JSON.parse(localStorage.getItem('highScores') || '[]');
  existingScores.push(score);
  const updatedScores = existingScores.sort((a: number, b: number) => b - a)
    .slice(0, MAX_HIGH_SCORES);
  localStorage.setItem('highScores', JSON.stringify(updatedScores));
}

/**
 * Retrieves high scores from localStorage.
 * Returns an array of scores sorted in descending order (highest first).
 * Handles corrupted data gracefully by returning an empty array.
 * 
 * @returns Array of high scores, sorted highest to lowest
 */
export function getHighScores(): number[] {
  try {
    const scores = JSON.parse(localStorage.getItem('highScores') || '[]');
    return Array.isArray(scores) ? scores.sort((a, b) => b - a).slice(0, MAX_HIGH_SCORES) : [];
  } catch {
    return [];
  }
}

/**
 * Enum defining different tick speeds for the game loop.
 * Controls how fast the game updates and pieces fall.
 */
enum TickSpeed {
  Normal = 800,   // Standard falling speed
  Sliding = 100,  // Speed when piece is about to lock in place
  Fast = 50,      // Speed when player holds down arrow
}

/**
 * Main Tetris game hook that manages all game state and logic.
 * Handles game initialization, user input, scoring, game loop timing,
 * and collision detection.
 * 
 * @returns Object containing game state and control functions
 */
export function useTetris() {
  const [score, setScore] = useState(0);
  const [upcomingBlocks, setUpcomingBlocks] = useState<Block[]>([]);
  const [isCommitting, setIsCommitting] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [tickSpeed, setTickSpeed] = useState<TickSpeed | null>(null);

  const [
    { board, droppingRow, droppingColumn, droppingBlock, droppingShape },
    dispatchBoardState,
  ] = useTetrisBoard();

  /**
   * Starts a new game by resetting all game state and initializing
   * the first set of upcoming blocks.
   */
  const startGame = useCallback(() => {
    const startingBlocks = [
      getRandomBlock(),
      getRandomBlock(),
      getRandomBlock(),
    ];
    setScore(0);
    setUpcomingBlocks(startingBlocks);
    setIsCommitting(false);
    setIsPlaying(true);
    setTickSpeed(TickSpeed.Normal);
    dispatchBoardState({ type: 'start' });
  }, [dispatchBoardState]);

  /**
   * Commits the current piece to the board when it can no longer fall.
   * Handles line clearing, scoring, spawning new pieces, and game over detection.
   */
  const commitPosition = useCallback(() => {
    // Check if piece can still fall - if so, don't commit yet
    if (!hasCollisions(board, droppingShape, droppingRow + 1, droppingColumn)) {
      setIsCommitting(false);
      setTickSpeed(TickSpeed.Normal);
      return;
    }

    // Add the current piece to the board
    const newBoard = structuredClone(board) as BoardShape;
    addShapeToBoard(
      newBoard,
      droppingBlock,
      droppingShape,
      droppingRow,
      droppingColumn
    );

    // Clear completed lines
    let numCleared = 0;
    for (let row = BOARD_HEIGHT - 1; row >= 0; row--) {
      if (newBoard[row].every((entry) => entry !== EmptyCell.Empty)) {
        numCleared++;
        newBoard.splice(row, 1);
      }
    }

    // Prepare next piece
    const newUpcomingBlocks = structuredClone(upcomingBlocks) as Block[];
    const newBlock = newUpcomingBlocks.pop() as Block;
    newUpcomingBlocks.unshift(getRandomBlock());

    // Check for game over (new piece collides immediately)
    if (hasCollisions(board, SHAPES[newBlock].shape, 0, 3)) {
      saveHighScore(score);
      setIsPlaying(false);
      setTickSpeed(null);
    } else {
      setTickSpeed(TickSpeed.Normal);
    }
    
    setUpcomingBlocks(newUpcomingBlocks);
    setScore((prevScore) => prevScore + getPoints(numCleared));
    dispatchBoardState({
      type: 'commit',
      newBoard: [...getEmptyBoard(BOARD_HEIGHT - newBoard.length), ...newBoard],
      newBlock,
    });
    setIsCommitting(false);
  }, [
    board,
    dispatchBoardState,
    droppingBlock,
    droppingColumn,
    droppingRow,
    droppingShape,
    upcomingBlocks,
    score,
  ]);

  /**
   * Main game tick function that handles piece movement and collision detection.
   * Called at regular intervals to progress the game state.
   */
  const gameTick = useCallback(() => {
    if (isCommitting) {
      commitPosition();
    } else if (
      hasCollisions(board, droppingShape, droppingRow + 1, droppingColumn)
    ) {
      // Piece can't fall further - start commit process
      setTickSpeed(TickSpeed.Sliding);
      setIsCommitting(true);
    } else {
      // Piece can fall - drop it one row
      dispatchBoardState({ type: 'drop' });
    }
  }, [
    board,
    commitPosition,
    dispatchBoardState,
    droppingColumn,
    droppingRow,
    droppingShape,
    isCommitting,
  ]);

  // Game loop - runs the game tick at the current tick speed
  useInterval(() => {
    if (!isPlaying) {
      return;
    }
    gameTick();
  }, tickSpeed);

  // Handle keyboard input for player controls
  useEffect(() => {
    if (!isPlaying) {
      return;
    }

    let isPressingLeft = false;
    let isPressingRight = false;
    let moveIntervalID: ReturnType<typeof setInterval> | undefined;

    /**
     * Updates the movement interval based on current key press state.
     * Handles continuous movement when arrow keys are held down.
     */
    const updateMovementInterval = () => {
      clearInterval(moveIntervalID);
      dispatchBoardState({
        type: 'move',
        isPressingLeft,
        isPressingRight,
      });
      moveIntervalID = setInterval(() => {
        dispatchBoardState({
          type: 'move',
          isPressingLeft,
          isPressingRight,
        });
      }, 300);
    };

    /**
     * Handles keydown events for player input.
     * Controls piece movement, rotation, and fast drop.
     */
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.repeat) {
        return;
      }

      if (event.key === 'ArrowDown') {
        setTickSpeed(TickSpeed.Fast);
      }

      if (event.key === 'ArrowUp') {
        dispatchBoardState({
          type: 'move',
          isRotating: true,
        });
      }

      if (event.key === 'ArrowLeft') {
        isPressingLeft = true;
        updateMovementInterval();
      }

      if (event.key === 'ArrowRight') {
        isPressingRight = true;
        updateMovementInterval();
      }
    };

    /**
     * Handles keyup events to stop continuous movement and fast drop.
     */
    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.key === 'ArrowDown') {
        setTickSpeed(TickSpeed.Normal);
      }

      if (event.key === 'ArrowLeft') {
        isPressingLeft = false;
        updateMovementInterval();
      }

      if (event.key === 'ArrowRight') {
        isPressingRight = false;
        updateMovementInterval();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
      clearInterval(moveIntervalID);
      setTickSpeed(TickSpeed.Normal);
    };
  }, [dispatchBoardState, isPlaying]);

  // Create the rendered board with the current dropping piece
  const renderedBoard = structuredClone(board) as BoardShape;
  if (isPlaying) {
    addShapeToBoard(
      renderedBoard,
      droppingBlock,
      droppingShape,
      droppingRow,
      droppingColumn
    );
  }

  return {
    board: renderedBoard,
    startGame,
    isPlaying,
    score,
    upcomingBlocks,
    highScores: getHighScores(),
  };
}

/**
 * Calculates points awarded based on the number of lines cleared simultaneously.
 * Awards bonus points for clearing multiple lines at once (Tetris bonus).
 * 
 * @param numCleared - Number of lines cleared in a single move
 * @returns Points awarded for the line clear
 */
function getPoints(numCleared: number): number {
  switch (numCleared) {
    case 0:
      return 0;
    case 1:
      return 100;   // Single line
    case 2:
      return 300;   // Double line
    case 3:
      return 500;   // Triple line
    case 4:
      return 800;   // Tetris (four lines)
    default:
      throw new Error('Unexpected number of rows cleared');
  }
}

/**
 * Adds a tetromino shape to the board at the specified position.
 * Updates the board array in-place by setting cells to the block type
 * where the shape has filled cells.
 * 
 * @param board - The game board to modify
 * @param droppingBlock - The type of block being placed
 * @param droppingShape - The shape pattern of the block
 * @param droppingRow - The row position to place the block
 * @param droppingColumn - The column position to place the block
 */
function addShapeToBoard(
  board: BoardShape,
  droppingBlock: Block,
  droppingShape: BlockShape,
  droppingRow: number,
  droppingColumn: number
) {
  droppingShape
    .filter((row) => row.some((isSet) => isSet))
    .forEach((row: boolean[], rowIndex: number) => {
      row.forEach((isSet: boolean, colIndex: number) => {
        if (isSet) {
          board[droppingRow + rowIndex][droppingColumn + colIndex] =
            droppingBlock;
        }
      });
    });
}
