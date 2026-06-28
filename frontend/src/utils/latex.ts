import katex from 'katex'
import 'katex/dist/katex.min.css'

/**
 * 将文本中的 $...$ 和 $$...$$ LaTeX 公式渲染为 HTML
 */
export function renderLatex(text: string): string {
  if (!text) return ''
  // $$...$$ display math
  let html = text.replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) => {
    try { return katex.renderToString(tex.trim(), { displayMode: true, throwOnError: false }) }
    catch { return tex }
  })
  // $...$ inline math (不匹配 \$ 转义)
  html = html.replace(/(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)/g, (_, tex) => {
    try { return katex.renderToString(tex.trim(), { displayMode: false, throwOnError: false }) }
    catch { return tex }
  })
  // 换行
  html = html.replace(/\n/g, '<br>')
  return html
}
