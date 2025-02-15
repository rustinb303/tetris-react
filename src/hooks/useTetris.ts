import    {useCallback, useEffect, useState } from 'react';
import      {Block, BlockShape, BoardShape, EmptyCell, SHAPES } from '../types';
import {  useInterval } from './useInterval';
import { useTetrisBoard, hasCollisions, BOARD_HEIGHT, getEmptyBoard, getRandomBlock,} from './useTetrisBoard';

const max_High_scores = 10;

/**
 * Saves a new high score to local storage.
 *
 * @param score - The score to save.
 */
export function saveHighScore(score: number): void {
  const existingScores = JSON.parse(localStorage.getItem('highScores') || '[]') as number[];
  existingScores.push(score);
  const updatedScores = existingScores.sort((a, b) => b - a).slice(0, max_High_scores);
  localStorage.setItem('highScores', JSON.stringify(updatedScores));
}

/**
 * Retrieves the high scores from local storage.
 *
 * @returns An array of high scores.
 */
export function GetHighScores(): number[] {
  try {
    const scores = JSON.parse(localStorage.getItem('highScores') || '[]') as number[];
    return Array.isArray(scores) ? scores.sort((a, b) => b - a).slice(0, max_High_scores) : [];
  } catch {
    return [];
  }
}

const max_High_scores = 10;

// this does something with the board, but I'm not sure what
enum TickSpeed {
  Normal = 800,
  Sliding = 100,
  Fast = 50,
}

// main function. todo: add comments
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
   * Starts the game.
   */
  const startGame = useCallback(() => {
    // Get the starting blocks.
    const startingBlocks = [
      getRandomBlock(),
      getRandomBlock(),
      getRandomBlock(),
    ];
    // Reset the score.
    setScore(0);
    // Set the upcoming blocks.
    setUpcomingBlocks(startingBlocks);
    // Set committing to false.
    setIsCommitting(false);
    // Set playing to true.
    setIsPlaying(true);
    // Set the tick speed to normal.
    setTickSpeed(TickSpeed.Normal);
    // Dispatch the start action.
    dispatchBoardState({ type: 'start' });
  }, [dispatchBoardState]);

  /**
   * Commits the position of the block on the board.
   */
  const commitPosition = useCallback(() => {
    // If there are no collisions, return.
    if (!hasCollisions(board, droppingShape, droppingRow + 1, droppingColumn)) {
      setIsCommitting(false);
      setTickSpeed(TickSpeed.Normal);
      return;
    }

    // Clone the current board.
    const newBoard = structuredClone(board) as BoardShape;
    // Add the current dropping shape to the board.
    addShapeToBoard(
      newBoard,
      droppingBlock,
      droppingShape,
      droppingRow,
      droppingColumn
    );

    // Calculate how many rows were cleared.
    let numCleared = 0;
    // Iterate from the bottom of the board.
    for (let row = BOARD_HEIGHT - 1; row >= 0; row--) {
      // Check if the row is full.
      if (newBoard[row].every((entry) => entry !== EmptyCell.Empty)) {
        numCleared++;
        // Remove the row.
        newBoard.splice(row, 1);
      }
    }

    // Get the next block.
    const newUpcomingBlocks = structuredClone(upcomingBlocks) as Block[];
    const newBlock = newUpcomingBlocks.pop() as Block;
    newUpcomingBlocks.unshift(getRandomBlock());

    // Check if there are collisions with the new block.
    if (hasCollisions(board, SHAPES[newBlock].shape, 0, 3)) {
      // Save the high score.
      saveHighScore(score);
      // Stop the game.
      setIsPlaying(false);
      setTickSpeed(null);
    } else {
      // Set the tick speed to normal.
      setTickSpeed(TickSpeed.Normal);
    }
    // Update the upcoming blocks.
    setUpcomingBlocks(newUpcomingBlocks);
    // Update the score.
    setScore((prevScore) => prevScore + getPoints(numCleared));
    // Update the board state.
    dispatchBoardState({
      type: 'commit',
      newBoard: [...getEmptyBoard(BOARD_HEIGHT - newBoard.length), ...newBoard],
      newBlock,
    });
    // Set committing to false.
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
   * Manages the game tick.
   */
  const gameTick = useCallback(() => {
    // If the game is committing, commit the position.
    if (isCommitting) {
      commitPosition();
    // If there are collisions, set the tick speed to sliding and set committing to true.
    } else if (
      hasCollisions(board, droppingShape, droppingRow + 1, droppingColumn)
    ) {
      setTickSpeed(TickSpeed.Sliding);
      setIsCommitting(true);
    // Otherwise, drop the block.
    } else {
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

  useInterval(() => {
    if (!isPlaying) {
      return;
    }
    gameTick();
  }, tickSpeed);

  useEffect(() => {
    if (!isPlaying) {
      return;
    }

  /**
   * Manages the keyboard events for moving the block.
   *
   * @param dispatchBoardState - The dispatch function to move the block.
   * @param isPlaying - Boolean indicating if the game is currently playing.
   * @returns A cleanup function.
   */
  /**
   * Manages the keyboard events for moving the block.
   *
   * @param dispatchBoardState - The dispatch function to move the block.
   * @param isPlaying - Boolean indicating if the game is currently playing.
   * @returns A cleanup function.
   */
  const useKeyboardControls = useCallback((
    dispatchBoardState: (arg: { type: string; isRotating?: boolean, isPressingLeft?: boolean, isPressingRight?: boolean }) => void,
    isPlaying: boolean
  ) => {
    // Define isPressingLeft and isPressingRight to false.
    let isPressingLeft = false;
    let isPressingRight = false;
    // Define the moveIntervalID.
    let moveIntervalID: ReturnType<typeof setInterval> | undefined;

    /**
     * Updates the movement interval.
     */
    const updateMovementInterval = () => {
      // Clear the moveIntervalID.
      clearInterval(moveIntervalID);
      // Dispatch the move action.
      dispatchBoardState({
        type: 'move',
        isPressingLeft,
        isPressingRight,
      });
      // Set the move interval.
      moveIntervalID = setInterval(() => {
        dispatchBoardState({
          type: 'move',
          isPressingLeft,
          isPressingRight,
        });
      }, 300);
    };

    /**
     * Handles the key down event.
     * 
     * @param event - The keyboard event.
     */
    const handleKeyDown = (event: KeyboardEvent) => {
      // If the key is pressed, then do not repeat.
      if (event.repeat) {
        return;
      }
      // If the key is the ArrowDown, set the tick speed to fast.
      if (event.key === 'ArrowDown') {
        setTickSpeed(TickSpeed.Fast);
      }

      // If the key is the ArrowUp, dispatch the move action with rotation.
      if (event.key === 'ArrowUp') {
        dispatchBoardState({
          type: 'move',
          isRotating: true,
        });
      }

      // If the key is the ArrowLeft, set isPressingLeft to true.
      if (event.key === 'ArrowLeft') {
        isPressingLeft = true;
        // Call the update movement interval.
        updateMovementInterval();
      }

      // If the key is the ArrowRight, set isPressingRight to true.
      if (event.key === 'ArrowRight') {
        isPressingRight = true;
        // Call the update movement interval.
        updateMovementInterval();
      }
    };

    /**
     * Handles the key up event.
     * 
     * @param event - The keyboard event.
     */
    const handleKeyUp = (event: KeyboardEvent) => {
      // If the key is the ArrowDown, set the tick speed to normal.
      if (event.key === 'ArrowDown') {
        setTickSpeed(TickSpeed.Normal);
      }
      // If the key is the ArrowLeft, set isPressingLeft to false.
      if (event.key === 'ArrowLeft') {
        isPressingLeft = false;
        // Call the update movement interval.
        updateMovementInterval();
      }
      // If the key is the ArrowRight, set isPressingRight to false.
      if (event.key === 'ArrowRight') {
        isPressingRight = false;
        // Call the update movement interval.
        updateMovementInterval();
      }
    };

    // Add the event listeners.
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);

    // Return the cleanup function.
    return () => {
      // Remove the event listeners.
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
      // Clear the interval.
      clearInterval(moveIntervalID);
      // Set the tick speed to normal.
      setTickSpeed(TickSpeed.Normal);
    };
  }, [dispatchBoardState, isPlaying]);

  /**
   * Manages the game keyboard controls.
   */
  useEffect(() => {
    // If the game is not playing, return.
    if (!isPlaying) {
      return;
    }
    // Call the useKeyboardControls function.
    return useKeyboardControls(dispatchBoardState, isPlaying);
  }, [dispatchBoardState, isPlaying]);

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
    highScores: GetHighScores(),
  };
}

/**
 * Calculates the points earned based on the number of rows cleared.
 *
 * @param numCleared - The number of rows cleared.
 * @returns The points earned.
 */
function getPoints(numCleared: number): number {
  const points = [0, 100, 300, 500, 800];
  if (numCleared < 0 || numCleared > points.length)
  {
    throw new Error('Unexpected number of rows cleared');
  }
  return points[numCleared];
}

/**
 * Adds the current dropping shape to the board.
 *
 * @param board - The game board.
 * @param droppingBlock - The current block.
 * @param droppingShape - The shape of the current block.
 * @param droppingRow - The current row.
 * @param droppingColumn - The current column.
 */
function addShapeToBoard(
  board: BoardShape,
  droppingBlock: Block,
  droppingShape: BlockShape,
  droppingRow: number,
  droppingColumn: number
) {
  droppingShape.forEach((row, rowIndex) => {
    row.forEach((isSet, colIndex) => {
      if (isSet) {
        board[droppingRow + rowIndex][droppingColumn + colIndex] = droppingBlock;
      }
    });
  });
}
