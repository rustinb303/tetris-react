import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import App from '../App';

describe('App', () => {
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
      render(<App />);
      expect(screen.getByText('No high scores yet!')).toBeInTheDocument();
    });
  });

  describe('Hardcore Mode Button', () => {
    it('toggles hardcore mode on button click', () => {
      render(<App />);

      // Button should be present when game is not playing
      const hardcoreButton = screen.getByRole('button', { name: /Enable Hardcore/i });
      expect(hardcoreButton).toBeInTheDocument();

      // Click to enable Hardcore mode
      fireEvent.click(hardcoreButton);
      expect(screen.getByRole('button', { name: /Disable Hardcore/i })).toBeInTheDocument();

      // Click to disable Hardcore mode
      fireEvent.click(hardcoreButton);
      expect(screen.getByRole('button', { name: /Enable Hardcore/i })).toBeInTheDocument();
    });

    it('hides Hardcore button when game is playing', () => {
      render(<App />);
      
      // Initially, the "Enable Hardcore" button should be visible
      expect(screen.getByRole('button', { name: /Enable Hardcore/i })).toBeInTheDocument();

      // Find and click the "New Game" button
      const newGameButton = screen.getByRole('button', { name: /New Game/i });
      fireEvent.click(newGameButton);

      // Now, the "Hardcore" button should not be visible
      expect(screen.queryByRole('button', { name: /Enable Hardcore/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Disable Hardcore/i })).not.toBeInTheDocument();
    });
  });
});
