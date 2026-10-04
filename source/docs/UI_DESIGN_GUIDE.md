# 视觉与交互规范

采用 macOS 工作台式清晰层级，结合教育产品的深青绿与柔和留白；借鉴 Apple 的设计原则，不复制其商标或独有素材。所有图形、字体回退、图标与动画资源离线提供。

主要颜色：正文 #202c34、品牌 #0d756f、页面背景 #f5f7f9、内容面板 #ffffff、次要文字 #667c73。正文与表格保持不透明；导航、弹窗遮罩适度使用模糊。卡片 14–20px 圆角、按钮 10px 圆角，阴影只用于层级分离。

登录页：CSS 渐变光晕、缓慢粒子漂移、卡片入场；主操作保持静止。工作台：分组卡片入场、首页轻浮动与低频扫光、骨架加载与顶部请求进度反馈、提交成功提示。动画不阻塞点击，也不自动改变业务状态。

演示导航：Alt+D 或页面底部按钮打开，逐步进入真实模块；聚焦展示降低导航视觉权重，悬停或键盘聚焦后恢复。演示导航只切换路由，不自动造数据。

交互动效以 transform/opacity 为主，CSS 与 Vue Transition 实现，不同时堆叠多个动画运行库。启用 prefers-reduced-motion 后停止循环和转场效果，内容仍可完整显示。

响应式：1440px 桌面与 390px 手机宽度已实际检查；小屏导航抽屉、筛选换行、内容单列，数据表格可横向滚动。弹窗支持 Escape、焦点圈与 Tab 焦点约束。生成的管理表单为控件提供明确可访问名称。

参考的一手资料：

- [Apple Motion](https://developer.apple.com/design/human-interface-guidelines/motion)
- [Apple Layout](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Apple Materials](https://developer.apple.com/design/human-interface-guidelines/materials)
- [Vue Transition](https://vuejs.org/guide/built-ins/transition)
- [Vue Performance](https://vuejs.org/guide/best-practices/performance.html)
- [web.dev 动画性能](https://web.dev/articles/animations-guide)
- [W3C 交互动效可访问性](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html)
- [Lucide Vue](https://lucide.dev/guide/packages/lucide-vue)

已安装并验证的辅助技能：Anthropic 前端设计、Vercel Web Design Guidelines、GSAP 五项技能及本地 Apple Web Design。Apple Web Design 是依据官方资料整理的本地技能，不是 Apple 官方发布的技能。本项目实际运行仅使用 CSS/Vue 动效，不依赖 GSAP 或外部 CDN。
