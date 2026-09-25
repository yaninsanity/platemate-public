// 只声明你真正会用到的那几个 API，保持简洁
declare module 'dom-to-image-more' {
  interface Options {
    width?: number;
    height?: number;
    bgcolor?: string;
    style?: Record<string, string>;
    filter?: (node: HTMLElement) => boolean;
    quality?: number;            // JPEG
    imagePlaceholder?: string;   // SVG
  }

  const domToImage: {
    toPng(node: HTMLElement, options?: Options): Promise<string>;
    toJpeg(node: HTMLElement, options?: Options): Promise<string>;
    toBlob(node: HTMLElement, options?: Options): Promise<Blob>;
    toSvg(node: HTMLElement, options?: Options): Promise<string>;
    // 补充其他方法时，再往下加
  };

  export = domToImage; // ← 兼容 commonjs 默认导出
}
