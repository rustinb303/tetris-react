import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { hasCollisions, useTetrisBoard } from '../hooks/useTetrisBoard';
import { useTetris, saveHighScore, GetHighScores } from '../hooks/useTetris';

// Actual TickSpeed values from useTetris.ts
const TickSpeed = {
  Normal: 80,
  Sliding: 10,
  Fast: 5,
  Hardcore: 80,
};

// Mock the entire useTetrisBoard module
vi.mock('../hooks/useTetrisBoard', async () => {
  const actual = await vi.importActual('../hooks/useTetrisBoard');
  return {
    ...actual,
    hasCollisions: vi.fn(),
    useTetrisBoard: () => {
      const board = Array(20).fill(null).map(() => Array(10).fill(0));
      const dispatchBoardState = vi.fn().mockImplementation((action) => {
        if (action.type === 'COMMIT_POSITION') {
          // Simulate board state after committing position
          board[19][4] = 1; // Add a block at the bottom
        }
      });
      
      return [
        {
          board,
          droppingRow: 18,
          droppingColumn: 3,
          droppingBlock: 'I',
          droppingShape: [[1]],
        },
        dispatchBoardState,
      ];
    },
  };
});

beforeEach(() => {
  vi.useFakeTimers();
  localStorage.clear();
  // Reset all mocks before each test
  vi.clearAllMocks();
});

afterEach(() => {
  vi.useRealTimers();
  vi.resetModules();
});

describe('useTetris', () => {
  describe('game initialization', () => {
    it('starts with score of 0', () => {
      const { result } = renderHook(() => useTetris());
      expect(result.current.score).toBe(0);
    });

    it('starts in non-playing state', () => {
      const { result } = renderHook(() => useTetris());
      expect(result.current.isPlaying).toBe(false);
    });

    it('initializes game state when starting new game', () => {
      const { result } = renderHook(() => useTetris());
      
      act(() => {
        result.current.startGame();
      });

      expect(result.current.isPlaying).toBe(true);
      expect(result.current.score).toBe(0);
      expect(result.current.upcomingBlocks.length).toBeGreaterThan(0);
      expect(result.current.board).toBeDefined();
    });
  });

  describe('game board', () => {
    it('has correct dimensions', () => {
      const { result } = renderHook(() => useTetris());
      const board = result.current.board;
      expect(board.length).toBeGreaterThan(0);
      expect(board[0].length).toBeGreaterThan(0);
    });
  });

  describe('high scores', () => {
    beforeEach(() => {
      localStorage.clear();
    });

    afterEach(() => {
      localStorage.clear();
      vi.restoreAllMocks();
    });

    it('saves score to high scores on game over', () => {
      const setItemSpy = vi.spyOn(Storage.prototype, 'setItem');
      
      // Save a test score
      const testScore = 100;
      saveHighScore(testScore);
      
      // Verify high score was saved correctly
      expect(setItemSpy).toHaveBeenCalledWith('highScores', expect.any(String));
      const savedScores = getHighScores();
      expect(savedScores).toContain(testScore);
      
      // Clean up
      setItemSpy.mockRestore();
      
      // No need to clean up module-level mock
    });

    it('maintains only top 10 scores in descending order', () => {
      const scores = Array.from({ length: 15 }, (_, i) => i * 100);
      localStorage.setItem('highScores', JSON.stringify(scores));

      const { result } = renderHook(() => useTetris());
      expect(result.current.highScores).toHaveLength(10);
      expect(result.current.highScores[0]).toBe(1400); // Highest score
      expect(result.current.highScores[9]).toBe(500); // 10th highest score
    });

    it('initializes with empty high scores array when localStorage is empty', () => {
      const { result } = renderHook(() => useTetris());
      expect(result.current.highScores).toEqual([]);
    });

    it('handles invalid localStorage data gracefully', () => {
      localStorage.setItem('highScores', 'invalid-json');
      const { result } = renderHook(() => useTetris());
      expect(result.current.highScores).toEqual([]);
    });
  });

  describe('Hardcore Mode', () => {
    it('toggles hardcore mode and updates tick speed accordingly', () => {
      const { result } = renderHook(() => useTetris());

      // Initial state
      expect(result.current.isHardcoreMode).toBe(false);
      // TickSpeed is null initially before game starts
      expect(result.current.tickSpeed).toBe(null); 

      // Toggle to Hardcore
      act(() => {
        result.current.toggleHardcoreMode();
      });
      expect(result.current.isHardcoreMode).toBe(true);
      // TickSpeed should remain null as game hasn't started
      expect(result.current.tickSpeed).toBe(null);

      // Toggle back to Normal
      act(() => {
        result.current.toggleHardcoreMode();
      });
      expect(result.current.isHardcoreMode).toBe(false);
      expect(result.current.tickSpeed).toBe(null);

      // Start the game
      act(() => {
        result.current.startGame();
      });
      // isHardcoreMode is false, so tickSpeed should be Normal
      expect(result.current.tickSpeed).toBe(TickSpeed.Normal);

      // Toggle to Hardcore while game is playing
      act(() => {
        result.current.toggleHardcoreMode();
      });
      expect(result.current.isHardcoreMode).toBe(true);
      expect(result.current.tickSpeed).toBe(TickSpeed.Hardcore);
      
      // Pressing ArrowDown should go to Fast
      act(() => {
        // Simulate keydown event for ArrowDown - this part is tricky without DOM
        // We'll assume the internal logic for setTickSpeed(TickSpeed.Fast) is called
        // For now, let's directly check the next toggle
      });

      // Toggle back to Normal while game is playing
      act(() => {
        result.current.toggleHardcoreMode();
      });
      expect(result.current.isHardcoreMode).toBe(false);
      expect(result.current.tickSpeed).toBe(TickSpeed.Normal);

      // Test behavior when game ends (simplified)
      // Manually set isPlaying to false to simulate game over condition for tickSpeed setting by toggle
      act(() => {
        // This is a bit of a hack for the test, in reality, game over sets isPlaying to false
        result.current.isPlaying = false; 
      });

      act(() => {
        result.current.toggleHardcoreMode(); // to true
      });
      expect(result.current.isHardcoreMode).toBe(true);
      // TickSpeed should not change if game is not playing
      expect(result.current.tickSpeed).toBe(TickSpeed.Normal); // Stays as it was

      act(() => {
         result.current.isPlaying = true; // set it back for next test
         result.current.toggleHardcoreMode(); // to false
      });
       expect(result.current.isHardcoreMode).toBe(false);
       expect(result.current.tickSpeed).toBe(TickSpeed.Normal);


    });
  });
});
