import { useCallback, useEffect, useState } from 'react';
import { Block, BlockShape, BoardShape, EmptyCell, SHAPES } from '../types';
import { useInterval } from './useInterval';
import { useTetrisBoard, hasCollisions, BOARD_HEIGHT, getEmptyBoard, getRandomBlock } from './useTetrisBoard';

const MAX_HIGH_SCORES = 10;

// Saves the high score to local storage.
export function saveHighScore(score: number): void {
  const existingScores = JSON.parse(localStorage.getItem('highScores') || '[]');
  existingScores.push(score);
  const updatedScores = existingScores
    .sort((a: number, b: number) => b - a)
    .slice(0, MAX_HIGH_SCORES);
  localStorage.setItem('highScores', JSON.stringify(updatedScores));
}

// Retrieves the high scores from local storage.
export function getHighScores(): number[] {
  try {
    const scores = JSON.parse(localStorage.getItem('highScores') || '[]');
    // Validate that scores is an array of numbers before sorting and slicing
    if (Array.isArray(scores) && scores.every(score => typeof score === 'number')) {
      return scores.sort((a, b) => b - a).slice(0, MAX_HIGH_SCORES);
    } else {
      // Handle cases where localStorage contains non-array or non-numeric data
      console.warn('High scores retrieved from localStorage is not a valid number array. Resetting.');
      localStorage.removeItem('highScores'); // Optional: Clear invalid data
      return [];
    }
  } catch (error) {
    // Log the error if JSON parsing or any other operation within the try block fails
    console.error('Failed to retrieve or parse high scores:', error);
    return [];
  }
}

// Defines the intervals (in milliseconds) for different game tick speeds.
enum TickSpeed {
  Normal = 800, // Standard falling speed.
  Sliding = 100, // Faster speed when the block hits the bottom, allowing for sliding.
  Fast = 50, // Very fast speed when holding the down arrow.
}

// Calculates points based on the number of lines cleared.
function getPoints(numCleared: number): number {
  switch (numCleared) {
    case 0:
      return 0;
    case 1:
      return 100; // Points for clearing 1 line.
    case 2:
      return 300; // Points for clearing 2 lines.
    case 3:
      return 500; // Points for clearing 3 lines.
    case 4:
      return 800; // Points for clearing 4 lines (Tetris).
    default:
      // This should not happen in standard Tetris.
      throw new Error('Unexpected number of rows cleared');
  }
}

/**
 * Adds the visual representation of the dropping piece onto a given board.
 * This function iterates through the piece's shape matrix and updates the
 * corresponding cells on the board with the piece's block type.
 * IMPORTANT: This function mutates the `board` object passed to it. It's intended
 * to be used on a *clone* of the main board state for rendering purposes.
 *
 * @param board The board (BoardShape) to draw the piece onto. This board WILL be mutated.
 * @param droppingBlock The type of block (color/enum) to draw.
 * @param droppingShape The 2D boolean array representing the piece's shape.
 * @param droppingRow The row index for the top of the piece on the board.
 * @param droppingColumn The column index for the left of the piece on the board.
 */
function addShapeToBoard(
  board: BoardShape, // The board to modify.
  droppingBlock: Block, // The type/color of the block to place.
  droppingShape: BlockShape,
  droppingRow: number, // Target row on the board.
  droppingColumn: number // Target column on the board.
) {
  // Iterate through each cell of the dropping shape's bounding box.
  droppingShape
    // Optimization: Skip rows in the shape definition that are entirely empty.
    .filter((row) => row.some((isSet) => isSet))
    .forEach((row: boolean[], rowIndex: number) => {
      row.forEach((isSet: boolean, colIndex: number) => {
        // Check if the current cell in the shape matrix is 'true' (part of the piece).
        if (isSet) {
          // Calculate the corresponding coordinates on the main game board.
          const boardRow = droppingRow + rowIndex;
          const boardCol = droppingColumn + colIndex;
          // Update the cell on the board with the block type (color/enum) of the dropping piece.
          // Note: This assumes the coordinates are valid and within the board boundaries,
          // which should be guaranteed by the collision detection logic before calling this.
          board[boardRow][boardCol] = droppingBlock;
        }
      });
    });
}

/**
 * Custom hook `useTetris`
 *
 * This hook encapsulates the entire logic for a Tetris game.
 * It manages the game board, the falling piece, player score,
 * upcoming blocks, game state (playing/paused), and input handling.
 * It utilizes `useTetrisBoard` for board state management and `useInterval`
 * for the game loop timing.
 *
 * @returns An object containing the game state and functions to control the game.
 */
export function useTetris() {
  // State variables for score, upcoming blocks, committing state, playing state, and tick speed.
  const [score, setScore] = useState(0);
  const [upcomingBlocks, setUpcomingBlocks] = useState<Block[]>([]);
  const [isCommitting, setIsCommitting] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [tickSpeed, setTickSpeed] = useState<TickSpeed | null>(null);

  const [
    { board, droppingRow, droppingColumn, droppingBlock, droppingShape },
    dispatchBoardState,
  ] = useTetrisBoard();

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
    // Initialize the board state when starting the game.
    dispatchBoardState({ type: 'start' });
  }, [dispatchBoardState]);

  /**
   * Commits the current dropping piece to the board.
   * This function is called when a piece can no longer move down or when
   * the player forces a commit (e.g., hard drop - though not implemented here).
   * It handles placing the piece, clearing completed lines, updating the score,
   * generating the next piece, and checking for game over conditions.
   */
  const commitPosition = useCallback(() => {
    // Check if the piece can still move down. If so, reset commit state and speed.
    // This allows the player to slide the piece shortly after it touches down.
    if (!hasCollisions(board, droppingShape, droppingRow + 1, droppingColumn)) {
      setIsCommitting(false);
      setTickSpeed(TickSpeed.Normal);
      return;
    }

    // The piece has landed and cannot move down further. Commit it to the board.
    console.log('Committing piece');
    const newBoard = structuredClone(board) as BoardShape;
    // Add the static shape of the landed piece to the board state.
    addShapeToBoard(
      newBoard,
      droppingBlock,
      droppingShape,
      droppingRow,
      droppingColumn
    );

    // --- Line Clearing ---
    let numCleared = 0;
    // Iterate through rows from bottom to top.
    for (let row = BOARD_HEIGHT - 1; row >= 0; row--) {
      // Check if the current row is completely filled with non-empty cells.
      if (newBoard[row].every((entry) => entry !== EmptyCell.Empty)) {
        numCleared++;
        // Remove the completed row from the board array.
        newBoard.splice(row, 1);
      }
    }

    // --- Generate Next Piece & Check Game Over ---
    // Create a copy of the upcoming blocks queue.
    const newUpcomingBlocks = structuredClone(upcomingBlocks) as Block[];
    // Get the next block from the end of the queue (it becomes the new dropping block).
    const newBlock = newUpcomingBlocks.pop() as Block;
    // Add a new random block to the start of the queue (will be shown as upcoming).
    newUpcomingBlocks.unshift(getRandomBlock());

    // Check if the newly spawned piece immediately collides with existing blocks.
    // Standard Tetris spawns pieces around row 0, column 3/4/5.
    // We use the *original* board for this check, before line clears,
    // to correctly handle cases where the new piece spawns into the space
    // that was just cleared.
    if (hasCollisions(board, SHAPES[newBlock].shape, 0, 3)) {
      // Game Over condition met.
      console.log('Game Over');
      saveHighScore(score); // Save the final score.
      setIsPlaying(false); // Stop the game.
      setTickSpeed(null); // Stop the game loop interval.
    } else {
      setTickSpeed(TickSpeed.Normal); // Continue playing with normal speed.
    }
    setUpcomingBlocks(newUpcomingBlocks); // Update the state for the upcoming blocks queue.
    setScore((prevScore) => prevScore + getPoints(numCleared)); // Add points for cleared lines.

    // --- Update Board State ---
    // Dispatch the commit action to update the board in the state reducer.
    // Prepend empty rows to the top of the board array to account for cleared lines.
    // Calculate the number of empty rows needed (equal to lines cleared).
    const emptyRows = getEmptyBoard(numCleared);
    dispatchBoardState({
      type: 'commit',
      // Create the final board state by adding empty rows above the modified board.
      newBoard: [...emptyRows, ...newBoard],
      newBlock, // Provide the next block to become the new dropping piece.
    });
    setIsCommitting(false); // Reset the committing flag.
  }, [
    board, // Depends on board for collision checks and modification.
    dispatchBoardState,
    droppingBlock,
    droppingColumn,
    droppingRow,
    droppingShape,
    upcomingBlocks,
    score, // Score is needed for the game over check.
  ]);

  /**
   * Represents a single step in the game loop (a 'tick').
   * It checks if the current piece should be committed or dropped further down.
   */
  const gameTick = useCallback(() => {
    // If the piece is in the 'committing' phase (meaning it hit something below
    // on the previous tick but wasn't locked yet), try committing it now.
    if (isCommitting) {
      commitPosition();
    }
    // Check if the piece will collide if moved one step down.
    else if (hasCollisions(board, droppingShape, droppingRow + 1, droppingColumn)) {
      // Collision detected below. Enter the 'committing' phase.
      // This gives the player a brief moment (TickSpeed.Sliding interval)
      // to slide the piece horizontally before it locks.
      setTickSpeed(TickSpeed.Sliding);
      setIsCommitting(true);
    } else {
      // No collision below, so simply move the piece one step down.
      dispatchBoardState({ type: 'drop' });
    }
  }, [
    board, // Depends on the current board state for collision checks.
    commitPosition,
    dispatchBoardState,
    droppingColumn,
    droppingRow,
    droppingShape, // Needed for collision checks.
    isCommitting, // Determines whether to commit or check for drop/slide.
  ]);

  // Sets up the main game loop interval using the useInterval hook.
  useInterval(() => {
    // The game loop should only run when `isPlaying` is true.
    if (!isPlaying) {
      return;
    }
    // Execute the core game logic for one tick.
    gameTick();
  }, tickSpeed); // The interval speed is controlled by the `tickSpeed` state variable.

  // Effect hook to handle keyboard input for controlling the piece.
  useEffect(() => {
    // Only listen for input if the game is currently playing.
    if (!isPlaying) {
      return;
    }

    let isPressingLeft = false;
    let isPressingRight = false;
    let moveIntervalID: ReturnType<typeof setInterval> | undefined;

    // Updates the movement interval based on pressed keys.
    const updateMovementInterval = () => {
      clearInterval(moveIntervalID); // Clear existing interval.
      // Dispatch the move action to the board reducer immediately on key press/release.
      dispatchBoardState({
        type: 'move', // Specifies the action type for the reducer.
        isPressingLeft,
        isPressingRight,
      });
      // Set up an interval to repeat the move action for smooth continuous movement
      // while the left or right key is held down.
      moveIntervalID = setInterval(() => {
        dispatchBoardState({
          type: 'move', // Specifies the action type for the reducer.
          isPressingLeft,
          isPressingRight,
        });
      }, 100); // Interval duration in milliseconds. Adjust for desired sensitivity.
    };

    // Handles the 'keydown' event.
    const handleKeyDown = (event: KeyboardEvent) => {
      // Prevent processing the event if the key is already being held down (event.repeat is true).
      // This is important for actions that should only trigger once per press (like rotation).
      if (event.repeat) {
        return;
      }

      // --- Down Arrow: Fast Drop ---
      if (event.key === 'ArrowDown') {
        // Set the game tick speed to Fast to make the piece fall quickly.
        setTickSpeed(TickSpeed.Fast);
      }

      if (event.key === 'ArrowUp') {
        // Rotate the block.
        dispatchBoardState({
          type: 'move',
          isRotating: true,
        });
      }

      if (event.key === 'ArrowLeft') {
        isPressingLeft = true;
        updateMovementInterval(); // Start moving left.
      }

      if (event.key === 'ArrowRight') {
        isPressingRight = true;
        updateMovementInterval(); // Start moving right.
      }
    };

    // Handles key up events.
    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.key === 'ArrowDown') {
        // Restore the normal tick speed when the down arrow is released.
        setTickSpeed(TickSpeed.Normal);
      }

      // --- Left Arrow: Stop Left Movement ---
      if (event.key === 'ArrowLeft') {
        isPressingLeft = false; // Update the flag.
        updateMovementInterval(); // Update the movement interval (will stop continuous left move).
      }

      // --- Right Arrow: Stop Right Movement ---
      if (event.key === 'ArrowRight') {
        isPressingRight = false; // Update the flag.
        updateMovementInterval(); // Update the movement interval (will stop continuous right move).
      }
    };

    // Add event listeners for keyboard input.
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);

    // Cleanup function to remove event listeners and clear intervals.
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
      clearInterval(moveIntervalID); // Clear the movement interval.
      // Reset tick speed to normal if the effect cleans up while speed is altered.
      // This prevents the game from staying in Fast/Sliding speed if paused/stopped externally.
      if (tickSpeed !== TickSpeed.Normal && tickSpeed !== null) {
         setTickSpeed(TickSpeed.Normal);
      }
    };
    // Dependencies: The effect should re-run if the board dispatcher, playing state, or tick speed changes.
  }, [dispatchBoardState, isPlaying, tickSpeed]);

  // --- Rendered Board Preparation ---
  // Create a deep clone of the current board state to avoid direct mutation.
  const renderedBoard = structuredClone(board) as BoardShape;
  // If the game is active, draw the currently dropping piece onto this cloned board.
  // This separates the static board state from the visual representation with the moving piece.
  if (isPlaying) {
    addShapeToBoard(
      renderedBoard, // Modify the cloned board.
      droppingBlock,
      droppingShape,
      droppingRow,
      droppingColumn
    );
  }

  // --- Hook Return Value ---
  // Expose the necessary state variables and control functions to the component using this hook.
  return {
    board: renderedBoard, // The board shape ready for rendering (includes the dropping piece).
    startGame, // Function to start a new game.
    isPlaying, // Boolean indicating if the game is currently active.
    score, // The current score.
    upcomingBlocks, // The list of upcoming blocks.
    highScores: getHighScores(), // Retrieves and returns the current high scores.
  };
}
