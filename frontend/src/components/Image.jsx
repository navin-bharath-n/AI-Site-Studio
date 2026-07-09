export default function Image({ src, alt, width, height, className, fill, ...props }) {
  const style = fill ? { position: 'absolute', height: '100%', width: '100%', left: 0, top: 0, right: 0, bottom: 0, color: 'transparent', objectFit: 'cover' } : {};
  return <img src={src} alt={alt || ''} width={width} height={height} className={className} style={style} {...props} />;
}
