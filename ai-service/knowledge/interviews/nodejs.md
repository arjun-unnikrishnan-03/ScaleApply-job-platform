# Node.js Interview Guide

## Core Concepts to Probe
- **Event Loop**: Can the candidate explain the phases of the event loop? (Timers, Pending Callbacks, Idle/Prepare, Poll, Check, Close Callbacks).
- **Asynchronous Programming**: Deep understanding of Promises, async/await, and avoiding callback hell.
- **Streams**: Knowledge of Readable, Writable, Duplex, and Transform streams. Why are streams important for memory management?

## Red Flags
- Blocking the event loop with synchronous operations (`fs.readFileSync` in request handlers).
- Not understanding memory leaks and garbage collection in V8.
- Ignoring unhandled promise rejections.
