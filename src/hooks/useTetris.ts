import { useCallback, useEffect, useState } from 'react';

import { Block, BlockShape, BoardShape, EmptyCell, SHAPES } from '../types';
import { useInterval } from './useInterval';
import {
  useTetrisBoard,
  hasCollisions,
  BOARD_HEIGHT,
  getEmptyBoard,
  getRandomBlock,
} from './useTetrisBoard';

const MAX_HIGH_SCORES = 10;

/**
 * Saves a new score to the high scores list in localStorage.
 * Keeps only the top MAX_HIGH_SCORES scores in descending order.
 * @param score - The score to save.
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
 * Scores are sorted in descending order and limited to MAX_HIGH_SCORES.
 * @returns An array of numbers representing the high scores, or an empty array if none are found or an error occurs.
 */
export function getHighScores(): number[] {
      try { const scores = JSON.parse(localStorage.getItem('highScores') || '[]');
    return Array.isArray(scores) ? scores.sort((a, b) => b - a).slice(0, MAX_HIGH_SCORES) : [];
  } catch {return [];
  }
}

enum TickSpeed {
  Normal = 800,
  Sliding = 100,
  Fast = 50,
}

/**
 * Custom hook to manage the Tetris game logic and state.
 * @returns An object containing the game board, functions to control the game (startGame),
 * current game status (isPlaying, score), upcoming blocks, and current high scores.
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
   * Initializes and starts a new Tetris game.
   * Resets the score, sets up initial upcoming blocks, enables playing state,
   * sets the tick speed to normal, and dispatches the 'start' action to the board state.
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
   * Commits the current dropping piece to the board.
   * This function is called when the piece can no longer move down or when the player forces it.
   * It checks for line clears, updates the score, prepares the next piece,
   * and handles game over conditions if the new piece causes a collision.
   */
  const commitPosition = useCallback(() => {
    if (!hasCollisions(board, droppingShape, droppingRow + 1, droppingColumn)) {
      setIsCommitting(false);
      setTickSpeed(TickSpeed.Normal);
      return;
    }

    // Deep clone the board to avoid modifying the state directly before dispatch
    const newBoard = structuredClone(board) as BoardShape;
    addShapeToBoard(
      newBoard,
      droppingBlock,
      droppingShape,
      droppingRow,
      droppingColumn
    );

    let numCleared = 0;
    for (let row = BOARD_HEIGHT - 1; row >= 0; row--) {
      if (newBoard[row].every((entry) => entry !== EmptyCell.Empty)) {
        numCleared++;
        newBoard.splice(row, 1);
      }
    }

    const newUpcomingBlocks = structuredClone(upcomingBlocks) as Block[];
    const newBlock = newUpcomingBlocks.pop() as Block;
    newUpcomingBlocks.unshift(getRandomBlock());

    // Check for game over: if the new block has immediate collisions
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
   * Represents a single tick of the game loop.
   * If the game is in a committing state, it calls `commitPosition`.
   * Otherwise, it checks for collisions below the current piece. If a collision occurs,
   * it sets the game to a committing state (allowing the player to slide the piece).
   * If no collision, it dispatches a 'drop' action to move the piece down.
   */
  const gameTick = useCallback(() => {
    if (isCommitting) {
      commitPosition();
    } else if (
      hasCollisions(board, droppingShape, droppingRow + 1, droppingColumn)
    ) {
      setTickSpeed(TickSpeed.Sliding);
      setIsCommitting(true);
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

  // Effect to handle keyboard inputs for controlling the Tetris game (movement, rotation, fast drop).
  useEffect(() => {
    if (!isPlaying) {
      return;
    }

    let isPressingLeft = false;
    let isPressingRight = false;
    let moveIntervalID: ReturnType<typeof setInterval> | undefined;

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
 * Calculates the points awarded based on the number of lines cleared.
 * @param numCleared - The number of lines cleared at once.
 * @returns The score points awarded.
 * @throws Error if an unexpected number of lines cleared is provided.
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
 * Adds the current dropping piece (shape) to the game board at the specified position.
 * This function mutates the `board` parameter directly.
 * @param board - The game board to modify.
 * @param droppingBlock - The type of block being dropped (e.g., 'I', 'T').
 * @param droppingShape - The current rotation shape of the block.
 * @param droppingRow - The row index for the top of the dropping shape.
 * @param droppingColumn - The column index for the left of the dropping shape.
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
