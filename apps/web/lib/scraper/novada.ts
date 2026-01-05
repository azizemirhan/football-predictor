
import { HttpsProxyAgent } from 'https-proxy-agent'; 

export interface NovadaConfig {
  host: string;
  port: number;
  username?: string;
  password?: string;
}

export class NovadaClient {
  private config: NovadaConfig;

  constructor(config?: Partial<NovadaConfig>) {
    this.config = {
      host: config?.host || process.env.NOVADA_PROXY_HOST || '',
      port: Number(config?.port || process.env.NOVADA_PROXY_PORT || 7777),
      username: config?.username || process.env.NOVADA_PROXY_USER,
      password: config?.password || process.env.NOVADA_PROXY_PASS
    };
  }

  getProxyUrl() {
    if (this.config.username && this.config.password) {
      return `http://${this.config.username}:${this.config.password}@${this.config.host}:${this.config.port}`;
    }
    return `http://${this.config.host}:${this.config.port}`;
  }
  
  getAnonymizedProxyUrl() {
     // For chrome args, usually simple format is better, auth handled via page.authenticate
     return `http://${this.config.host}:${this.config.port}`;
  }
}
