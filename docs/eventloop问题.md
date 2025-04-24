1. 事件循环关闭时序冲突​​
在release_connection中异步操作（如`conn.reset()`）触发时，事件循环可能处于`_closing`或`_stopping`状态
Windows平台ProactorEventLoop在关闭时仍尝试执行_ProactorBasePipeTransport的异步清理操作

2. 