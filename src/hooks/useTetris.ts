/**
 * useTetris.ts
 *
 * This file contains the main game logic hook for the Tetris game.
 * It manages game state, score tracking, block movement, collision detection,
 * keyboard input handling, and high score persistence using localStorage.
 */

import { useCallback, useEffect, useState } from 'react';
import { Block, BlockShape, BoardShape, EmptyCell, SHAPES } from '../types';
import { useInterval } from './useInterval';
import { useTetrisBoard, hasCollisions, BOARD_HEIGHT, getEmptyBoard, getRandomBlock } from './useTetrisBoard';

// Maximum number of high scores to keep in localStorage
const MAX_HIGH_SCORES = 10;

/**
 * Saves a new score to the high scores list in localStorage.
 * Maintains only the top MAX_HIGH_SCORES scores in descending order.
 *
 * @param score - The score to save
 * @returns void
 */
export function saveHighScore(score: number): void {
  const existingScores = JSON.parse(localStorage.getItem('highScores') || '[]');
  existingScores.push(score);
  const updatedScores = existingScores.sort((a: number, b: number) => b - a)
    .slice(0, MAX_HIGH_SCORES);
  localStorage.setItem('highScores', JSON.stringify(updatedScores));
}

/**
 * Retrieves the list of high scores from localStorage.
 * Returns an empty array if localStorage is unavailable or data is corrupted.
 *
 * @returns Array of high scores in descending order
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
 * Enum defining the different tick speeds for the game loop.
 * These control how fast blocks fall during different game states.
 */
enum TickSpeed {
  Normal = 800,  // Normal falling speed
  Sliding = 100, // Speed when block is about to commit
  Fast = 50,     // Speed when player holds down arrow
}

/**
 * Main Tetris game hook that manages all game state and logic.
 * Handles block dropping, rotation, collision detection, scoring, and keyboard input.
 *
 * @returns Object containing game board, control functions, and game state
 */
export function useTetris() {
  // Game state
  const [score, setScore] = useState(0);
  const [upcomingBlocks, setUpcomingBlocks] = useState<Block[]>([]);
  const [isCommitting, setIsCommitting] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [tickSpeed, setTickSpeed] = useState<TickSpeed | null>(null);

  // Board state from useTetrisBoard hook
  const [
    { board, droppingRow, droppingColumn, droppingBlock, droppingShape },
    dispatchBoardState,
  ] = useTetrisBoard();

  /**
   * Starts a new game by initializing all game state.
   * Creates starting blocks, resets score, and begins the game loop.
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
   * Commits the current block to the board when it can no longer fall.
   * Checks for completed rows, updates score, spawns new block, and handles game over.
   */
  const commitPosition = useCallback(() => {
    // If block can still fall, don't commit yet
    if (!hasCollisions(board, droppingShape, droppingRow + 1, droppingColumn)) {
      setIsCommitting(false);
      setTickSpeed(TickSpeed.Normal);
      return;
    }

    // Create a copy of the board and add the current block to it
    const newBoard = structuredClone(board) as BoardShape;
    addShapeToBoard(
      newBoard,
      droppingBlock,
      droppingShape,
      droppingRow,
      droppingColumn
    );

    // Check for completed rows and remove them
    let numCleared = 0;
    for (let row = BOARD_HEIGHT - 1; row >= 0; row--) {
      if (newBoard[row].every((entry) => entry !== EmptyCell.Empty)) {
        numCleared++;
        newBoard.splice(row, 1);
      }
    }

    // Get next block from upcoming blocks and generate a new one
    const newUpcomingBlocks = structuredClone(upcomingBlocks) as Block[];
    const newBlock = newUpcomingBlocks.pop() as Block;
    newUpcomingBlocks.unshift(getRandomBlock());

    // Check for game over (new block collides immediately)
    if (hasCollisions(board, SHAPES[newBlock].shape, 0, 3)) {
      saveHighScore(score);
      setIsPlaying(false);
      setTickSpeed(null);
    } else {
      setTickSpeed(TickSpeed.Normal);
    }

    // Update game state
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
   * Main game tick function that runs on each interval.
   * Handles block dropping, collision detection, and position committing.
   */
  const gameTick = useCallback(() => {
    if (isCommitting) {
      commitPosition();
    } else if (
      hasCollisions(board, droppingShape, droppingRow + 1, droppingColumn)
    ) {
      // Block hit something, start commit countdown
      setTickSpeed(TickSpeed.Sliding);
      setIsCommitting(true);
    } else {
      // Continue dropping block
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

  // Run the game tick at the current tick speed
  useInterval(() => {
    if (!isPlaying) {
      return;
    }
    gameTick();
  }, tickSpeed);

  /**
   * Effect hook for handling keyboard input.
   * Manages continuous movement when arrow keys are held down,
   * fast drop, and block rotation.
   */
  useEffect(() => {
    if (!isPlaying) {
      return;
    }

    let isPressingLeft = false;
    let isPressingRight = false;
    let moveIntervalID: ReturnType<typeof setInterval> | undefined;

    /**
     * Updates the movement interval based on current key press state.
     * Clears previous interval and starts a new one for continuous movement.
     */
    const updateMovementInterval = () => {
      clearInterval(moveIntervalID);
      dispatchBoardState({
        type: 'move',
        isPressingLeft,
        isPressingRight,
      });
      // Continue moving every 300ms while key is held
      moveIntervalID = setInterval(() => {
        dispatchBoardState({
          type: 'move',
          isPressingLeft,
          isPressingRight,
        });
      }, 300);
    };

    /**
     * Handles keydown events for game controls.
     * ArrowDown: Fast drop, ArrowUp: Rotate, ArrowLeft/Right: Move
     */
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignore repeated keydown events from holding key
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
     * Handles keyup events to stop continuous movement or fast drop.
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

    // Register event listeners
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);

    // Cleanup function to remove listeners and intervals
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
      clearInterval(moveIntervalID);
      setTickSpeed(TickSpeed.Normal);
    };
  }, [dispatchBoardState, isPlaying]);

  // Create a rendered version of the board with the current dropping block
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
 * Calculates points awarded based on number of rows cleared simultaneously.
 * Rewards clearing multiple rows at once with exponentially higher scores.
 *
 * @param numCleared - Number of rows cleared (0-4)
 * @returns Points awarded for the cleared rows
 * @throws Error if numCleared is outside valid range
 */
function getPoints(numCleared: number): number {
  switch (numCleared) {
    case 0:
      return 0;
    case 1:
      return 100;
    case 2:
      return 300;
    case 3:
      return 500;
    case 4:
      return 800;
    default:
      throw new Error('Unexpected number of rows cleared');
  }
}

/**
 * Adds a block shape to the board at the specified position.
 * Modifies the board in place by setting cells to the block type.
 *
 * @param board - The game board to modify
 * @param droppingBlock - The type of block being added
 * @param droppingShape - The shape matrix of the block
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
