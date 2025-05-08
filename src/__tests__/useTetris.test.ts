import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTetrisBoard } from '../hooks/useTetrisBoard'; // Only import types/methods used by mock
import { useTetris, saveHighScore, GetHighScores } from '../hooks/useTetris';

// Import hasCollisions separately to mock it effectively
import * as TetrisBoardHooks from '../hooks/useTetrisBoard';

// Updated TickSpeed values to match the new enum structure in useTetris.ts
const TickSpeed = {
  Normal: 800,
  Sliding: 100,
  Fast: 50,
  HardcoreNormal: 80,
  HardcoreSliding: 10,
  HardcoreFast: 5,
};

// Spy on addEventListener and removeEventListener
const addEventListenerSpy = vi.spyOn(document, 'addEventListener');
const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener');


// Mock the entire useTetrisBoard module
vi.mock('../hooks/useTetrisBoard', async () => {
  const actual = await vi.importActual<typeof TetrisBoardHooks>('../hooks/useTetrisBoard');
  return {
    ...actual, // Spread actual implementation
    hasCollisions: vi.fn(), // Mock hasCollisions specifically
    // Keep the rest of useTetrisBoard's mock as it was if needed, or simplify
    useTetrisBoard: () => {
      const board = Array(20).fill(null).map(() => Array(10).fill(0));
      const dispatchBoardState = vi.fn();
      return [
        {
          board,
          droppingRow: 18, // Example values
          droppingColumn: 3,
          droppingBlock: 'I',
          droppingShape: [[true]], // Simplified shape
        },
        dispatchBoardState,
      ];
    },
  };
});

// Access the mock for hasCollisions that was defined in the first vi.mock call
const mockedHasCollisions = TetrisBoardHooks.hasCollisions as vi.Mock;
// We also need a reference to the dispatch function from the *active* mock of useTetrisBoard
// This is tricky because vi.mock is hoisted. Let's ensure one definitive mock.
// The first vi.mock is more detailed, let's remove the second simpler one.
// The spy setup for addEventListener/removeEventListener is good.

// This dispatch mock will be used by the useTetrisBoard mock
const mockedDispatchBoardState = vi.fn();

// Re-assert the intended mock for useTetrisBoard to avoid confusion from previous duplicate
vi.mocked(TetrisBoardHooks.useTetrisBoard).mockImplementation(() => {
  const board = TetrisBoardHooks.getEmptyBoard(); // Use actual utility
  // Ensure this mockedDispatchBoardState is the one returned and used
  mockedDispatchBoardState.mockClear(); // Clear for each hook re-render if necessary
  return [
    {
      board,
      droppingRow: 0,
      droppingColumn: 3, // Center column for a standard board
      droppingBlock: 'I', // Default block
      droppingShape: TetrisBoardHooks.SHAPES.I.shape, // Default shape
    },
    mockedDispatchBoardState, // Return the spy
  ];
});


beforeEach(() => {
  vi.useFakeTimers();
  localStorage.clear();
  // Reset all mocks before each test
  vi.clearAllMocks(); // This clears spies like addEventListenerSpy too.
  
  // Default mock behavior for hasCollisions (no collision) for each test
  mockedHasCollisions.mockReturnValue(false);
  // Clear specific mocks that might have state from other tests if not covered by clearAllMocks
  mockedDispatchBoardState.mockClear(); // Ensure dispatch is clean
});

afterEach(() => {
  vi.useRealTimers();
  // vi.resetModules(); // Generally not needed with Vitest's default ESM mocking
});

describe('useTetris Hook', () => {
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

  describe('Hardcore Mode Toggling and Start Game', () => {
    it('initializes with isHardcoreMode false and null tickSpeed', () => {
      const { result } = renderHook(() => useTetris());
      expect(result.current.isHardcoreMode).toBe(false);
      expect(result.current.tickSpeed).toBe(null);
    });

    it('toggles isHardcoreMode state correctly', () => {
      const { result } = renderHook(() => useTetris());
      act(() => result.current.toggleHardcoreMode());
      expect(result.current.isHardcoreMode).toBe(true);
      act(() => result.current.toggleHardcoreMode());
      expect(result.current.isHardcoreMode).toBe(false);
    });

    it('sets correct initial tickSpeed on startGame based on isHardcoreMode', () => {
      const { result } = renderHook(() => useTetris());

      // Start game in Normal mode (isHardcoreMode is false by default)
      act(() => result.current.startGame());
      expect(result.current.tickSpeed).toBe(TickSpeed.Normal); // 800

      // Simulate ending game & toggling mode before next start
      act(() => {
        result.current.isPlaying = false; // Manual override for test simplicity
        result.current.tickSpeed = null;  // Reset tick speed
        result.current.toggleHardcoreMode(); // Enable hardcore
      });
      expect(result.current.isHardcoreMode).toBe(true);
      
      // Start game in Hardcore mode
      act(() => result.current.startGame());
      expect(result.current.tickSpeed).toBe(TickSpeed.HardcoreNormal); // 80
    });

    it('updates tickSpeed when toggling Hardcore mode during an active game', () => {
      const { result } = renderHook(() => useTetris());
      act(() => result.current.startGame()); // Game starts, isHardcoreMode=false, speed=Normal (800)
      expect(result.current.tickSpeed).toBe(TickSpeed.Normal);

      act(() => result.current.toggleHardcoreMode()); // Toggle to Hardcore
      expect(result.current.isHardcoreMode).toBe(true);
      expect(result.current.tickSpeed).toBe(TickSpeed.HardcoreNormal); // 80

      act(() => result.current.toggleHardcoreMode()); // Toggle back to Normal
      expect(result.current.isHardcoreMode).toBe(false);
      expect(result.current.tickSpeed).toBe(TickSpeed.Normal); // 800
    });

    it('does not change tickSpeed when toggling Hardcore mode if game is not playing', () => {
      const { result } = renderHook(() => useTetris());
      expect(result.current.isPlaying).toBe(false);
      expect(result.current.tickSpeed).toBe(null);

      act(() => result.current.toggleHardcoreMode()); // To true
      expect(result.current.isHardcoreMode).toBe(true);
      expect(result.current.tickSpeed).toBe(null); // Should remain null

      act(() => result.current.toggleHardcoreMode()); // To false
      expect(result.current.isHardcoreMode).toBe(false);
      expect(result.current.tickSpeed).toBe(null); // Should remain null
    });
  });

  describe('In-Game Speed Mechanics (Normal and Hardcore)', () => {
    let keydownHandler: ((event: Partial<KeyboardEvent>) => void) | undefined;
    let keyupHandler: ((event: Partial<KeyboardEvent>) => void) | undefined;

    beforeEach(() => {
      // Clear previous handlers
      keydownHandler = undefined;
      keyupHandler = undefined;
      // Capture event handlers attached by useEffect in useTetris
      addEventListenerSpy.mockImplementation((event, handler) => {
        if (event === 'keydown') keydownHandler = handler as any;
        if (event === 'keyup') keyupHandler = handler as any;
      });
    });
    
    afterEach(() => {
      // Ensure event listeners are cleaned up (implicitly by unmount or game stop)
      // Spies are cleared in global beforeEach
    });

    it('handles fast drop speeds (ArrowDown) correctly', () => {
      const { result } = renderHook(() => useTetris());
      
      act(() => result.current.startGame()); // isHardcoreMode is false initially
      expect(result.current.tickSpeed).toBe(TickSpeed.Normal); // 800
      act(() => { if (keydownHandler) keydownHandler({ key: 'ArrowDown' }); });
      expect(result.current.tickSpeed).toBe(TickSpeed.Fast); // 50
      act(() => { if (keyupHandler) keyupHandler({ key: 'ArrowDown' }); });
      expect(result.current.tickSpeed).toBe(TickSpeed.Normal); // 800

      act(() => result.current.toggleHardcoreMode()); // Toggle to Hardcore
      expect(result.current.tickSpeed).toBe(TickSpeed.HardcoreNormal); // 80 (speed changes on toggle)
      act(() => { if (keydownHandler) keydownHandler({ key: 'ArrowDown' }); });
      expect(result.current.tickSpeed).toBe(TickSpeed.HardcoreFast); // 5
      act(() => { if (keyupHandler) keyupHandler({ key: 'ArrowDown' }); });
      expect(result.current.tickSpeed).toBe(TickSpeed.HardcoreNormal); // 80
    });

    it('handles sliding speeds correctly', () => {
      const { result } = renderHook(() => useTetris());

      // Test in Normal Mode
      act(() => result.current.startGame());
      expect(result.current.tickSpeed).toBe(TickSpeed.Normal); // 800
      
      mockedHasCollisions.mockReturnValue(true); // Simulate collision
      act(() => result.current.gameTick()); // gameTick checks collision, sets isCommitting, changes speed
      expect(result.current.tickSpeed).toBe(TickSpeed.Sliding); // 100
      expect(result.current.isCommitting).toBe(true);
      
      mockedHasCollisions.mockReturnValue(false); // No more collision for commit logic
      // The next gameTick will call commitPosition because isCommitting is true
      act(() => result.current.gameTick()); 
      expect(result.current.tickSpeed).toBe(TickSpeed.Normal); // 800 (commitPosition resets to Normal)
      expect(result.current.isCommitting).toBe(false);

      // Toggle to Hardcore mode and test again
      act(() => result.current.toggleHardcoreMode());
      expect(result.current.tickSpeed).toBe(TickSpeed.HardcoreNormal); // 80

      mockedHasCollisions.mockReturnValue(true); // Simulate collision
      act(() => result.current.gameTick());
      expect(result.current.tickSpeed).toBe(TickSpeed.HardcoreSliding); // 10
      expect(result.current.isCommitting).toBe(true);
      
      mockedHasCollisions.mockReturnValue(false); // No more collision
      act(() => result.current.gameTick()); 
      expect(result.current.tickSpeed).toBe(TickSpeed.HardcoreNormal); // 80
      expect(result.current.isCommitting).toBe(false);
    });

    it('useEffect cleanup removes event listeners when game is active', () => {
      const { result, unmount } = renderHook(() => useTetris());
      // Start game to ensure listeners are active
      act(() => result.current.startGame()); 
      // At this point, keydownHandler and keyupHandler should have been captured by addEventListenerSpy
      expect(keydownHandler).toBeDefined();
      expect(keyupHandler).toBeDefined();
      
      unmount(); 
      expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', keydownHandler);
      expect(removeEventListenerSpy).toHaveBeenCalledWith('keyup', keyupHandler);
    });

     it('useEffect cleanup is robust even if listeners were not set', () => {
      const { unmount } = renderHook(() => useTetris());
      // Game not started, isPlaying is false, so listeners might not be added by useEffect.
      // keydownHandler and keyupHandler would be undefined here.
      expect(keydownHandler).toBeUndefined();
      expect(keyupHandler).toBeUndefined();
      
      unmount(); 
      // removeEventListener should still be called with undefined or the placeholder if that's how the hook is written
      // More importantly, it doesn't crash.
      // The spy will record calls with 'undefined' if the handler was undefined.
      expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', undefined);
      expect(removeEventListenerSpy).toHaveBeenCalledWith('keyup', undefined);
    });
  });
});
