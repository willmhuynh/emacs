;;; read-aloud-autoloads.el --- automatically extracted autoloads
;;
;;; Code:

(add-to-list 'load-path (directory-file-name
                         (or (file-name-directory #$) (car load-path))))


;;;### (autoloads nil "read-aloud" "read-aloud.el" (0 0 0 0))
;;; Generated autoloads from read-aloud.el

(autoload 'read-aloud-change-engine "read-aloud" "\
Select another TTS engine.

\(fn)" t nil)

(autoload 'read-aloud-stop "read-aloud" "\
Ask a TTS engine to stop.

\(fn)" t nil)

(autoload 'read-aloud-buf "read-aloud" "\
Read the current buffer, highlighting words along the
read. Run it again to stop reading.

\(fn)" t nil)

(autoload 'read-aloud-this "read-aloud" "\
Pronounce either the selection or a word under the pointer.

\(fn)" t nil)

(if (fboundp 'register-definition-prefixes) (register-definition-prefixes "read-aloud" '("read-aloud-")))

;;;***

;; Local Variables:
;; version-control: never
;; no-byte-compile: t
;; no-update-autoloads: t
;; coding: utf-8
;; End:
;;; read-aloud-autoloads.el ends here
