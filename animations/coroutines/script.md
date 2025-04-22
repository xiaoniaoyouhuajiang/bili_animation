动画核心目标： 清晰展示两个纤程（Thread 1 和 Thread 2）如何在单个 OS 线程上，通过 Runtime、switch 函数和各自独立的栈实现并发执行和上下文切换。

动画元素预设：
OS Thread: 一个大的外框，表示所有活动都发生在这个单线程内。
CPU: 一个简化的 CPU 图标，包含关键寄存器（特别是 rsp, rip，以及几个 callee-saved 寄存器如 rbx, rbp, r12-r15）。寄存器内的值需要动态变化。
Runtime: 一个表示 Runtime 结构体的方框，包含：
threads: 一个数组/列表，存放 Thread 对象。
current: 一个指针/高亮，指示当前正在运行的 Thread 的索引。
Thread 对象 (纤程): 两个或多个（以两个为例，T1 和 T2）方框，每个包含：
stack: 一块可视化的内存区域（用垂直条或矩形表示），需要能显示栈指针 rsp 的位置和少量关键数据（如函数地址）。
ctx (ThreadContext): 一个小的关联方框，用于存放保存的寄存器值。需要能显示其 rsp 和其他 callee-saved 寄存器的值。
state: 显示当前状态 (Available, Ready, Running)。
代码片段: 在关键步骤旁边显示对应的 Rust 或汇编代码片段。
箭头和高亮: 用于指示控制流、数据流动和当前活动区域。

动画流程描述（分阶段）：
阶段 1：初始化 Runtime 和 Spawn 第一个纤程 (T1)
场景: OS Thread 框内，显示 main 函数代码片段。
动作:
let mut runtime = Runtime::new();: Runtime 方框出现，threads 数组初始化（包含 base_thread T0，状态 Running，以及 T1, T2 等状态 Available），current 指向 T0。
runtime.init();: 一个全局 RUNTIME 指针（可以简化表示）指向 Runtime 方框。（这一步可以简化或省略动画，说明即可）。
runtime.spawn(|| { /* T1 code */ });:
高亮显示 spawn 函数代码。
Runtime 查找 Available 的 Thread，找到 T1，高亮 T1。
关键步骤 - 设置 T1 的栈：
放大 T1 的 stack 区域。
显示计算 stack_bottom 和 sb_aligned 的过程（可以简化为最终指向栈顶附近）。
在栈顶特定偏移位置（如 -16）写入 guard 函数的地址（用 G 表示）。
在 -24 位置写入 skip 函数地址（用 S 表示，如果书中实现有）。
在 -32 位置写入 T1 要执行的函数 f1 的地址（用 F1 表示）。
高亮 T1 的 ctx.rsp 字段，并将其值设置为指向栈上 F1 地址的那个地址。 （例如 0x...20）。
将 T1 的 state 从 Available 变为 Ready。
阶段 2：Spawn 第二个纤程 (T2)
场景: 同上。
动作:
runtime.spawn(|| { /* T2 code */ });: 重复阶段 1 的 spawn 过程，但作用于 T2。
查找 Available 找到 T2。
设置 T2 的 stack，在相应位置写入 G, S, F2（T2 的函数地址）。
设置 T2 的 ctx.rsp 指向其栈上 F2 的地址。
T2 的 state 变为 Ready。
阶段 3：开始运行 (runtime.run()) - 第一次 Yield (从 T0 到 T1)
场景: main 函数调用 runtime.run()，进入 run 函数的循环，调用 t_yield()。
动作:
高亮 t_yield 函数代码。
调度:
current 指向 T0 (状态 Running)。
循环查找 Ready 状态的 Thread。
找到 T1，高亮 T1。
状态转换:
T0 的 state 变为 Ready (base_thread 通常保持特殊状态，这里简化)。
T1 的 state 变为 Running。
准备切换:
获取 T0 的 ctx 地址 (old_ctx) 和 T1 的 ctx 地址 (new_ctx)。
高亮 call switch 或 RegContext::swap 调用。
进入 switch / swap_registers (核心动画):
放大 CPU 寄存器区域。
保存 T0 上下文:
CPU 的 callee-saved 寄存器、rsp、rip (或 lr/ra) 的值，通过箭头复制到 T0 的 ctx 存储区域中。
（rip 的保存比较特殊，通常是 call 指令隐式压栈的返回地址，或者 ret 要用的地址，动画可以简化表示为保存当前指令的下一个地址）。
加载 T1 上下文:
T1 的 ctx 中存储的值（特别是我们之前设置的初始 rsp，指向 T1 栈上 F1 地址；其他 callee-saved 寄存器此时是 0 或默认值），通过箭头复制到 CPU 对应的寄存器中。 CPU 的 rsp 变为指向 T1 栈！
跳转:
CPU 执行 ret (或 br/jr)。
CPU 从新的 rsp 指向的地址（T1 栈上的 F1 地址）加载值 F1 到 rip。
rsp 增加。
切换完成:
CPU 的 rip 指向 F1 的第一条指令。
控制流箭头指向 T1 的代码片段（f1 函数）。
Runtime 的 current 指针更新指向 T1。
CPU 开始执行 T1 的代码。
阶段 4：T1 执行并 Yield
场景: CPU 正在执行 T1 的代码（例如 println!, 循环计数）。
动作:
T1 代码执行，可能会有一些栈操作（rsp 在 T1 的栈上移动）。
执行到 yield_thread() (或类似的调用，最终触发 t_yield)。
高亮 t_yield 调用。
进入 t_yield 函数:
调度:
current 指向 T1。
查找下一个 Ready 状态的 Thread，找到 T2。
状态转换:
T1 的 state 变为 Ready。
T2 的 state 变为 Running。
准备切换: 获取 T1 的 ctx (old_ctx) 和 T2 的 ctx (new_ctx)。
进入 switch / swap_registers:
保存 T1 上下文: 将 CPU 当前的 callee-saved, rsp (指向 T1 栈的当前位置), rip (指向 yield_thread 返回后的位置) 保存到 T1 的 ctx 中。
加载 T2 上下文: 将 T2 的 ctx 中的初始 rsp (指向 T2 栈上的 F2 地址) 和其他寄存器值 加载到 CPU。CPU rsp 变为指向 T2 栈！
跳转: ret 指令从新的 rsp 加载 F2 地址到 rip。
切换完成: CPU 开始执行 T2 的代码 (f2)，Runtime 的 current 指向 T2。
阶段 5：T2 执行并 Yield，切换回 T1
场景: CPU 正在执行 T2 的代码。
动作:
T2 代码执行。
执行到 yield_thread()。
进入 t_yield:
调度: 找到 T1 (状态 Ready)。
状态转换: T2 变 Ready，T1 变 Running。
准备切换: 获取 T2 ctx (old_ctx) 和 T1 ctx (new_ctx)。
进入 switch / swap_registers:
保存 T2 上下文: 保存 T2 的寄存器状态到 T2 ctx。
加载 T1 上下文: 关键点来了！ 这次从 T1 ctx 中加载的是上次 T1 yield 时保存的状态。CPU 的 rsp 恢复到 T1 栈上次暂停的位置，rip 恢复到 yield_thread 调用之后的位置，其他 callee-saved 寄存器也恢复。
跳转: ret 指令跳转到 T1 上次暂停的地方。
切换完成: CPU 从 T1 暂停的地方无缝恢复执行，Runtime current 指向 T1。
阶段 6：纤程结束 (以 T1 为例)
场景: T1 的函数 f1 执行完毕，即将从 f1 返回。
动作:
f1 执行 ret 指令（正常的函数返回）。
CPU 从 T1 栈上弹出返回地址。这个返回地址是我们当初在 spawn 时放在栈上的 guard 函数地址 (G)！
rip 指向 guard 函数，CPU 开始执行 guard 函数。
guard 函数执行:
获取 Runtime 指针。
将 T1 的 state 设置为 Available。
调用 t_yield()。
进入 t_yield:
调度: 找到 T2 (状态 Ready)。
状态转换: T1 变 Available，T2 变 Running。
准备切换: 获取 T1 ctx (old_ctx) 和 T2 ctx (new_ctx)。
进入 switch / swap_registers: 保存 T1（guard 函数调用 t_yield 时）的上下文，加载 T2 的上下文。
跳转: CPU 跳转到 T2 上次暂停的地方。
后续: T1 不再会被调度（除非重新 spawn）。
阶段 7：所有纤程结束
场景: T2 也执行完毕并调用 guard -> t_yield。
动作:
t_yield 循环查找，发现除了 T0 外，没有其他 Ready 状态的 Thread。
如果 current 回到了 T0，并且没有其他 Ready 的，t_yield 返回 false。
runtime.run() 的循环结束。
main 函数执行完毕（或者 std::process::exit(0)）。