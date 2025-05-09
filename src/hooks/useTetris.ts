import    {useCallback, useEffect, useState } from 'react';
import      {Block, BlockShape, BoardShape, EmptyCell, SHAPES } from '../types';
import {  useInterval } from './useInterval';
import { useTetrisBoard, hasCollisions, BOARD_HEIGHT, getEmptyBoard, getRandomBlock,} from './useTetrisBoard';

const MAX_HIGH_SCORES = 10;

/**
 * Saves the given score to the local storage if it's among the top N scores.
 * @param score The score to save.
 */
export function saveHighScore(score: number): void {
  const existingScores = JSON.parse(localStorage.getItem('highScores') || '[]');
  existingScores.push(score);
  const updatedScores = existingScores.sort((a: number, b: number) => b - a)
    .slice(0, MAX_HIGH_SCORES);
    localStorage.setItem('highScores', JSON.stringify(updatedScores));
}

/**
 * Retrieves the top N high scores from local storage.
 * @returns An array of high scores, sorted in descending order.
 */
export function getHighScores(): number[] {
      try { const scores = JSON.parse(localStorage.getItem('highScores') || '[]');
    return Array.isArray(scores) ? scores.sort((a, b) => b - a).slice(0, MAX_HIGH_SCORES) : [];
  } catch {return [];
  }
}

/**
 * Enum representing the speed of the game tick.
 * Normal: Standard game speed.
 * Sliding: Speed when a block is about to commit.
 * Fast: Speed when the player is actively pushing the block down.
 */
enum TickSpeed {
  Normal = 800,
  Sliding = 100,
  Fast = 50,
}

/**
 * Custom hook for managing the Tetris game logic.
 *
 * @returns An object containing the game state and functions to control the game.
 *  - board: The current state of the game board.
 *  - startGame: Function to start a new game.
 *  - isPlaying: Boolean indicating whether the game is currently active.
 *  - score: The current score of the player.
 *  - upcomingBlocks: An array of the next blocks that will appear.
 *  - highScores: An array of the top high scores.
 */
export function useTetris() {
  const [score, setScore] = useState(0);
  const [upcomingBlocks, setUpcomingBlocks] = useState<Block[]>([]);
  const [isCommitting, setIsCommitting] = useState(false); // Flag to indicate if a block is about to be committed to the board
  const [isPlaying, setIsPlaying] = useState(false); // Flag to indicate if the game is currently being played
  const [tickSpeed, setTickSpeed] = useState<TickSpeed | null>(null); // Current speed of the game tick

  const [
    { board, droppingRow, droppingColumn, droppingBlock, droppingShape }, // Destructure state from useTetrisBoard hook
    dispatchBoardState, // Dispatch function from useTetrisBoard hook
  ] = useTetrisBoard();

  /**
   * Starts a new game by initializing the game state.
   */
  const startGame = useCallback(() => {
    const startingBlocks = [ // Initialize with three random blocks
      getRandomBlock(),
      getRandomBlock(),
      getRandomBlock(),
    ];
    setScore(0); // Reset score
    setUpcomingBlocks(startingBlocks); // Set upcoming blocks
    setIsCommitting(false); // Reset committing flag
    setIsPlaying(true); // Set playing flag to true
    setTickSpeed(TickSpeed.Normal); // Set normal tick speed
    dispatchBoardState({ type: 'start' }); // Dispatch start action to board state
  }, [dispatchBoardState]);

  /**
   * Commits the current dropping block to the board.
   * This function handles clearing lines, updating the score,
   * and checking for game over conditions.
   */
  const commitPosition = useCallback(() => {
    // If the block can move down further, it's not ready to be committed yet.
    if (!hasCollisions(board, droppingShape, droppingRow + 1, droppingColumn)) {
      setIsCommitting(false); // Reset committing flag
      setTickSpeed(TickSpeed.Normal); // Reset tick speed to normal
      return;
    }

    // Clone the board to make changes
    let newBoard = structuredClone(board) as BoardShape;
    // Add the dropping shape to the new board
    newBoard = addShapeToBoard(
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
        newBoard.splice(row, 1); // Remove the cleared row
      }
    }

    // Update upcoming blocks
    const newUpcomingBlocks = structuredClone(upcomingBlocks) as Block[];
    const newBlock = newUpcomingBlocks.pop() as Block; // Get the next block
    newUpcomingBlocks.unshift(getRandomBlock()); // Add a new random block to the queue

    // Check for game over: if the new block collides at the starting position
    if (hasCollisions(board, SHAPES[newBlock].shape, 0, 3)) {
      saveHighScore(score); // Save the current score
      setIsPlaying(false); // Set playing flag to false
      setTickSpeed(null); // Stop the game tick
    } else {
      setTickSpeed(TickSpeed.Normal); // Reset tick speed to normal
    }
    setUpcomingBlocks(newUpcomingBlocks); // Update the upcoming blocks state
    setScore((prevScore) => prevScore + getPoints(numCleared)); // Update the score
    dispatchBoardState({
      type: 'commit',
      // Add empty rows at the top to maintain board height after clearing lines
      newBoard: [...getEmptyBoard(BOARD_HEIGHT - newBoard.length), ...newBoard],
      newBlock, // Provide the new block to the board state
    });
    setIsCommitting(false); // Reset committing flag
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
   * Handles the game tick logic.
   * If a block is committing, it calls `commitPosition`.
   * If a block has collided, it sets the tick speed to `Sliding` and sets `isCommitting` to true.
   * Otherwise, it dispatches a 'drop' action to move the block down.
   */
  const gameTick = useCallback(() => {
    if (isCommitting) {
      commitPosition();
    } else if (
      hasCollisions(board, droppingShape, droppingRow + 1, droppingColumn)
    ) {
      setTickSpeed(TickSpeed.Sliding); // Block is about to commit, slow down for player to adjust
      setIsCommitting(true);
    } else {
      dispatchBoardState({ type: 'drop' }); // Move block down
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

  // Custom hook to run the game tick at the specified interval
  useInterval(() => {
    if (!isPlaying) {
      return;
    }
    gameTick();
  }, tickSpeed);

  // Effect hook to handle keyboard input for controlling the game
  useEffect(() => {
    if (!isPlaying) {
      return;
    }

    let isPressingLeft = false; // Flag for left arrow key press
    let isPressingRight = false; // Flag for right arrow key press
    let moveIntervalID: ReturnType<typeof setInterval> | undefined; // Interval ID for continuous movement

    /**
     * Updates the movement interval based on which arrow keys are pressed.
     * This allows for continuous movement when a key is held down.
     */
    const updateMovementInterval = () => {
      clearInterval(moveIntervalID); // Clear existing interval
      // Dispatch move action to the board state
      dispatchBoardState({
        type: 'move',
        isPressingLeft,
        isPressingRight,
      });
      // Set a new interval for continuous movement
      moveIntervalID = setInterval(() => {
        dispatchBoardState({
          type: 'move',
          isPressingLeft,
          isPressingRight,
        });
      }, 300); // Adjust this value for movement speed
    };

    /**
     * Handles keydown events for game controls.
     * - ArrowDown: Speeds up the block drop.
     * - ArrowUp: Rotates the block.
     * - ArrowLeft: Moves the block left.
     * - ArrowRight: Moves the block right.
     */
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.repeat) { // Ignore repeated events from holding a key down (handled by interval)
        return;
      }

      if (event.key === 'ArrowDown') {
        setTickSpeed(TickSpeed.Fast); // Speed up block drop
      }

      if (event.key === 'ArrowUp') {
        dispatchBoardState({
          type: 'move',
          isRotating: true, // Rotate the block
        });
      }

      if (event.key === 'ArrowLeft') {
        isPressingLeft = true;
        updateMovementInterval(); // Start continuous left movement
      }

      if (event.key === 'ArrowRight') {
        isPressingRight = true;
        updateMovementInterval(); // Start continuous right movement
      }
    };

    /**
     * Handles keyup events to stop actions.
     * - ArrowDown: Resets drop speed to normal.
     * - ArrowLeft: Stops left movement.
     * - ArrowRight: Stops right movement.
     */
    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.key === 'ArrowDown') {
        setTickSpeed(TickSpeed.Normal); // Reset drop speed
      }

      if (event.key === 'ArrowLeft') {
        isPressingLeft = false;
        updateMovementInterval(); // Stop left movement
      }

      if (event.key === 'ArrowRight') {
        isPressingRight = false;
        updateMovementInterval(); // Stop right movement
      }
    };

    // Add event listeners for keyboard input
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);
    // Cleanup function to remove event listeners and clear intervals when the component unmounts or `isPlaying` changes
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
      clearInterval(moveIntervalID);
      setTickSpeed(TickSpeed.Normal); // Reset tick speed on cleanup
    };
  }, [dispatchBoardState, isPlaying]);

  // Create a clone of the board to render, including the currently dropping piece
  let renderedBoard = structuredClone(board) as BoardShape;
  if (isPlaying) {
    // Add the currently dropping shape to the rendered board for display
    renderedBoard = addShapeToBoard(
      renderedBoard,
      droppingBlock,
      droppingShape,
      droppingRow,
      droppingColumn
    );
  }

  return {
    board: renderedBoard, // The game board with the current piece
    startGame, // Function to start the game
    isPlaying, // Game status
    score, // Current score
    upcomingBlocks, // Next blocks in the queue
    highScores: getHighScores(), // Top high scores
  };
}

/**
 * Calculates the points awarded based on the number of lines cleared.
 * @param numCleared The number of lines cleared.
 * @returns The points awarded.
 */
function getPoints(numCleared: number): number {
  switch (numCleared) {
    case 0:
      return 0; // No points for clearing 0 lines
    case 1:
      return 100; // Points for clearing 1 line
    case 2:
      return 300; // Points for clearing 2 lines
    case 3:
      return 500; // Points for clearing 3 lines
    case 4:
      return 800; // Points for clearing 4 lines (Tetris)
    default:
      throw new Error('Unexpected number of rows cleared'); // Should not happen
  }
}

/**
 * Adds a Tetris block shape to the game board at the specified position.
 *
 * @param board The game board to modify.
 * @param droppingBlock The type of block being dropped.
 * @param droppingShape The shape of the block being dropped.
 * @param droppingRow The row index where the top of the block is.
 * @param droppingColumn The column index where the left of the block is.
 * @returns A new board with the shape added.
 */
function addShapeToBoard(
  board: BoardShape, // The game board
  droppingBlock: Block, // The type of the block (e.g., T, L, Z)
  droppingShape: BlockShape, // The 2D array representing the block's shape
  droppingRow: number, // The row to place the top-left of the shape
  droppingColumn: number // The column to place the top-left of the shape
): BoardShape {
  const newBoard = structuredClone(board) as BoardShape;
  droppingShape
    .filter((row) => row.some((isSet) => isSet)) // Filter out empty rows in the shape
    .forEach((row: boolean[], rowIndex: number) => {
      row.forEach((isSet: boolean, colIndex: number) => {
        if (isSet) { // If the cell in the shape is set
          // Place the block on the new board at the corresponding position
          newBoard[droppingRow + rowIndex][droppingColumn + colIndex] =
            droppingBlock;
        }
      });
    });
  return newBoard;
}
