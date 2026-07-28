import { create } from 'zustand';

interface PipelineState {
  reset: () => void;
}

export const usePipelineStore = create<PipelineState>((set) => ({
  reset: () => {
    // Reset state placeholder for Phase 1
    console.log("Pipeline store reset called");
  },
}));
