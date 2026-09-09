export type TTSRequest = {
  text: string;
  voice?: string;
  outputPath: string;
};

export interface TTSProvider {
  synthesize(request:TTSRequest):Promise<string>;
}

/**
 * Implement this interface with the chosen TTS provider.
 * API keys must be supplied through environment variables, never committed to the project.
 */
export class ExternalTTSProvider implements TTSProvider {
  async synthesize(request:TTSRequest):Promise<string>{
    throw new Error("TTS provider not configured. Add a provider adapter without hard-coding credentials.");
  }
}
