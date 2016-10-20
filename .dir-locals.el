;;; Directory Local Variables
;;; For more information see (info "(emacs) Directory Variables")

((python-mode
  (eval highlight-regexp "TODO" 'hilight-yellow)
  (eval setenv "PYTHONPATH" (expand-file-name (vc-git-root (buffer-file-name))))
  (python-shell-interpreter . "python3")))
