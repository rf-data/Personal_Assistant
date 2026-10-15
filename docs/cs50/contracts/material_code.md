# Source files v1

UTF-8/BOM text import for py/sql/js/html/css/c/h/txt/md. Raw bytes/hash are stored
before parsing. Each line becomes a code block, preserving line endings, original
URL path (decoded and traversal-checked), language, binding and exact line number.
No AST execution, package installation or repository cloning. Invalid encoding,
NUL/binary content and empty files fail clearly. HTML tagged source_code remains
literal code when it is a file; source directory indexes remain HTML references.
ZIP/PPTX/archive payloads are never extracted. Eight targeted offline tests pass.
