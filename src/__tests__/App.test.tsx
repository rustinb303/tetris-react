import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import App from '../App';
import { useTetris } from '../hooks/useTetris'; // Import useTetris to mock

// Mock the useTetris hook
vi.mock('../hooks/useTetris');

const mockUseTetris = useTetris as vi.MockedFunction<typeof useTetris>;

describe('App', () => {
  const defaultMockValues = {
    board: Array(20).fill(Array(10).fill(0)), // Example board
    startGame: vi.fn(),
    isPlaying: false,
    score: 0,
    upcomingBlocks: [], // Example upcoming blocks
    isHardcoreMode: false,
    toggleHardcoreMode: vi.fn(),
    highScores: [],
  };

  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();
    // Provide a default implementation for useTetris
    mockUseTetris.mockReturnValue(defaultMockValues);
  });

  it('renders tetris app without crashing', () => {
    render(<App />);
    
    // Check for title
    expect(screen.getByText('Tetris')).toBeInTheDocument();
    
    // Check for New Game button (initial state)
    expect(screen.getByText('New Game')).toBeInTheDocument();
    
    // Check for score
    expect(screen.getByText(/Score:/)).toBeInTheDocument();
    
    // Check for game board (should be present even when not playing)
    expect(screen.getByRole('grid')).toBeInTheDocument();
  });

  describe('high scores integration', () => {
    beforeEach(() => {
      localStorage.clear();
    });

    afterEach(() => {
      localStorage.clear();
    });

    it('shows high scores when game is not being played', () => {
      const scores = [300, 200, 100];
      localStorage.setItem('highScores', JSON.stringify(scores));
      
      render(<App />);
      
      expect(screen.getByText('High Scores')).toBeInTheDocument();
      expect(screen.getByText('300')).toBeInTheDocument();
      expect(screen.getByText('200')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });

    it('shows "No high scores yet!" when there are no scores', () => {
      // This test might need adjustment if isPlaying is true by default in some scenarios
      mockUseTetris.mockReturnValue({ ...defaultMockValues, isPlaying: false, highScores: [] });
      render(<App />);
      expect(screen.getByText('No high scores yet!')).toBeInTheDocument();
    });
  });

  describe('Hardcore Mode Button', () => {
    it('renders "Enable Hardcore" button when game is not playing and hardcore is disabled', () => {
      mockUseTetris.mockReturnValue({
        ...defaultMockValues,
        isPlaying: false,
        isHardcoreMode: false,
      });
      render(<App />);
      expect(screen.getByRole('button', { name: /enable hardcore/i })).toBeInTheDocument();
    });

    it('renders "Disable Hardcore" button when game is not playing and hardcore is enabled', () => {
      mockUseTetris.mockReturnValue({
        ...defaultMockValues,
        isPlaying: false,
        isHardcoreMode: true,
      });
      render(<App />);
      expect(screen.getByRole('button', { name: /disable hardcore/i })).toBeInTheDocument();
    });

    it('renders "Enable Hardcore" button when game is playing and hardcore is disabled', () => {
      mockUseTetris.mockReturnValue({
        ...defaultMockValues,
        isPlaying: true,
        isHardcoreMode: false,
      });
      render(<App />);
      expect(screen.getByRole('button', { name: /enable hardcore/i })).toBeInTheDocument();
    });

    it('renders "Disable Hardcore" button when game is playing and hardcore is enabled', () => {
      mockUseTetris.mockReturnValue({
        ...defaultMockValues,
        isPlaying: true,
        isHardcoreMode: true,
      });
      render(<App />);
      expect(screen.getByRole('button', { name: /disable hardcore/i })).toBeInTheDocument();
    });

    it('calls toggleHardcoreMode when the Hardcore button is clicked (game not playing)', () => {
      const mockToggle = vi.fn();
      mockUseTetris.mockReturnValue({
        ...defaultMockValues,
        isPlaying: false,
        isHardcoreMode: false,
        toggleHardcoreMode: mockToggle,
      });
      render(<App />);
      const hardcoreButton = screen.getByRole('button', { name: /enable hardcore/i });
      fireEvent.click(hardcoreButton);
      expect(mockToggle).toHaveBeenCalledTimes(1);
    });

    it('calls toggleHardcoreMode when the Hardcore button is clicked (game playing)', () => {
      const mockToggle = vi.fn();
      mockUseTetris.mockReturnValue({
        ...defaultMockValues,
        isPlaying: true,
        isHardcoreMode: false, // State of isHardcoreMode doesn't matter for click itself
        toggleHardcoreMode: mockToggle,
      });
      render(<App />);
      // Button text will be "Enable Hardcore" due to isHardcoreMode: false
      const hardcoreButton = screen.getByRole('button', { name: /enable hardcore/i });
      fireEvent.click(hardcoreButton);
      expect(mockToggle).toHaveBeenCalledTimes(1);
    });
  });
});
