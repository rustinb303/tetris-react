import { useCallback, useEffect, useState } from 'react';
import { Block, BlockShape, BoardShape, EmptyCell, SHAPES } from '../types';
import { useInterval } from './useInterval';
import { useTetrisBoard, hasCollisions, BOARD_HEIGHT, getEmptyBoard, getRandomBlock } from './useTetrisBoard';

const MOVEMENT_INTERVAL = 300;

const MAX_HIGH_SCORES = 10;

/**
 * Saves a new high score to local storage.
 * @param score - The score to save.
 */
export function saveHighScore(score: number): void {
  const existingScores = JSON.parse(localStorage.getItem('highScores') || '[]');
  existingScores.push(score);
  const updatedScores = existingScores.sort((a: number, b: number) => b - a).slice(0, MAX_HIGH_SCORES);
  localStorage.setItem('highScores', JSON.stringify(updatedScores));
}

/**
 * Gets the current high scores from local storage.
 * @returns The high scores.
 */
export function getHighScores(): number[] {
  try {
    const scores = JSON.parse(localStorage.getItem('highScores') || '[]');
    return Array.isArray(scores) ? scores.sort((a, b) => b - a).slice(0, MAX_HIGH_SCORES) : [];
  } catch {
    return [];
  }
}

// this does something with the board, but I'm not sure what
enum TickSpeed {
  Normal = 800,
  Sliding = 100,
  Fast = 50,
}

/**
 * Main hook for the Tetris game logic.
 * @returns The game state and controls.
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
   * Starts a new game.
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
   * Commits the current position to the board.
   */
  const commitPosition = useCallback(() => {
    if (!hasCollisions(board, droppingShape, droppingRow + 1, droppingColumn)) {
      setIsCommitting(false);
      setTickSpeed(TickSpeed.Normal);
      return;
    }

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
   * Handles a single game tick.
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
      }, MOVEMENT_INTERVAL);
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
    highScores: GetHighScores(),
  };
}

/**
 * Calculates the number of points to award for each row cleared.
 * @param numCleared - The number of rows cleared.
 * @returns The number of points awarded.
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
 * Adds a shape to the board.
 * @param board - The board to modify.
 * @param droppingBlock - The block to add.
 * @param droppingShape - The shape of the block.
 * @param droppingRow - The row to drop the block in.
 * @param droppingColumn - The column to drop the block in.
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
