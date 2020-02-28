					; if init ain't loading, package-install ivy
(package-initialize)
;(ivy-mode 1)

(require 'org-learn)
(require 'org-drill)
(setq org-image-actual-width nil)
(require 'org-annotate-file)
(require 'org-bookmark)
(require 'org-panel)
(require 'org-toc)
(require 'image+)

(setq inhibit-startup-message 1)
;; Place this file in C:\Users\Username\AppData\Roaming and point to the appropriate files
(setq default-directory "C:/Users/Will/Documents/emacs")
(setenv "HOME" "C:/Users/Will/Documents/emacs")

(setq user-init-file "/.emacs")
(setq user-emacs-directory "~/.emacs.d/")
(add-to-list 'load-path "~/.emacs.d/elpa")
;;(load "anki-cards.el")
(let ((default-directory "~/.emacs.d/"))
  (normal-top-level-add-subdirs-to-load-path))
(setq org-agenda-files (quote ("~/Feb20.org")))
(load-file "~/.emacs.d/elpa/read-aloud/read-aloud.el")
(add-to-list 'load-path "~/.emacs.d/elpa/tts-mode")
(setq read-aloud-engine "jampal")
;; configure tts engine's command path if needed ;
;(setq espeak-program "E:/emacs/Programs/eSpeak/TTSApp") ;
;(setq festival-program "E:/emacs/.emacs.d/elpa/tts-mode/festival") ;
;(setq say-program "E:/emacs/.emacs.d/elpa/tts-mode/say");
;(setq espeak-program "E:/emacs/.emacs.d/elpa/tts-mode/espeak") ;
;(setq festival-program "E:/emacs/.emacs.d/elpa/tts-mode/festival") ;
;(setq say-program "E:/emacs/.emacs.d/elpa/tts-mode/say");

;; image settings
(setq org-image-actual-width nil)

;; The following lines are always needed.  Choose your own keys.

;; Added by Package.el.  This must come before configurations of
;; installed packages.  Don't delete this line.  If you don't want it,
;; just comment it out by adding a semicolon to the start of the line.
;; You may delete these explanatory comments.

;; Global Set Keys!
(global-set-key (kbd "\C-cl") 'org-store-link)
(global-set-key (kbd "\C-ca") 'org-agenda)
(global-set-key (kbd "\C-cc") 'org-capture)
(global-set-key (kbd "\C-cb") 'org-switchb)
(global-set-key (kbd "C-s") 'swiper)
(global-set-key (kbd "C-c d") 'org-drill)
(global-set-key (kbd "C-c n") 'org-annotate-file)
(global-set-key (kbd "C-c t") 'org-toc-show)
(global-set-key (kbd "C-c p") 'org-panel)
(global-set-key (kbd "C-c m") 'list-bookmarks)
(global-set-key (kbd "C-c s") 'bookmark-set)
(global-set-key [C-mouse-wheel-up-event]  'text-scale-increase)
(global-set-key  [C-mouse-wheel-down-event] 'text-scale-decrease)(global-set-key [C-mouse-4] 'text-scale-increase)
(global-set-key [C-mouse-5] 'text-scale-decrease)
(defadvice text-scale-increase (around all-buffers (arg) activate)
  (dolist (buffer (buffer-list))
    (with-current-buffer buffer
      ad-do-it)))

;; this is the start of William's Shit lol
;; Completion Framework: Ivy / Swiper / Counsel

;;Macros
;Mind Palace
(fset 'mpx
      (lambda (&optional arg) "Keyboard macro." (interactive "p") (kmacro-exec-ring-item (quote ([tab 58 80 82 79 80 69 82 84 73 69 83 58 return tab 58 83 85 66 74 69 67 84 58 return tab 58 84 79 80 73 67 58 return tab 58 84 65 71 83 58 return tab 58 69 78 68 58 up up up up] 0 "%d")) arg)))
;Anki Editor Card Basic
(fset 'aex
   (lambda (&optional arg) "Keyboard macro." (interactive "p") (kmacro-exec-ring-item (quote ([tab 58 80 82 79 80 69 82 84 73 69 83 58 return tab 58 65 78 75 73 95 68 69 67 75 58 32 48 101 109 97 99 115 return tab 58 65 78 75 73 95 78 79 84 69 95 84 89 80 69 58 32 66 97 115 105 99 return tab 58 65 78 75 73 95 84 65 71 83 58 return tab 58 69 78 68 58 C-return M-right 70 114 111 110 116 return M-return 66 97 99 107 return] 0 "%d")) arg)))
;Quick Link
(fset 'ql
   (lambda (&optional arg) "Keyboard macro." (interactive "p") (kmacro-exec-ring-item (quote ([67108896 1 23 91 91 69 59 47 101 109 97 99 115 47 68 66 47 77 80 47 25 46 111 114 103 93 91 25 93 93] 0 "%d")) arg)))
;Read aloud
(fset 'ra
   (lambda (&optional arg) "Keyboard macro." (interactive "p") (kmacro-exec-ring-item (quote ([134217848 114 101 97 100 32 97 108 111 117 100 32 98 117 102 return] 0 "%d")) arg)))
;Read stop
(fset 'rs
   (lambda (&optional arg) "Keyboard macro." (interactive "p") (kmacro-exec-ring-item (quote ("\370read aloud stop" 0 "%d")) arg)))

;; Annotation
(defun bookmark-show-org-annotations ()
  "Opens the annotations window for the currently selected bookmark file."
  (interactive)
  (bookmark-bmenu-other-window)
  (org-annotate-file)
  ;; or, if you're using the http://bitbucket.org/nickdaly/org-annotate-file fork,
  ;; (org-annotate-file-show-annotations)
  )

;;SRoskamp dotemacs
(require 'package)
(setq package-enable-at-startup nil)
;(let* ((no-ssl (and (memq system-type '(windows-nt ms-dos))
;                    (not (gnutls-available-p)))
;       (proto (if no-ssl "http" "https"))
(add-to-list 'package-archives '("melpa" . "https://melpa.org/packages/"))
(add-to-list 'package-archives ' ("gnu" . "http://elpa.gnu.org/packages/"))
;(org-babel-load-file "~.emacs.d/config.org")


;; Org Settings
(setq org-tag-alist '(("GIR" . ?g) ("HO" . ?h) ("CardioPulmEndo" . ?c) ("NeuroPsy" . ?n)("MSK" . ?m)("Repro" . ?r))) 
(setq org-log-done 'time)
(setq org-my-anki-file "E:/emacs/0rg/Anki.org")
(setq org-capture-templates
;%^g prompts for tag
      '(("t" "Todo" entry (file+headline "E:/emacs/0rg/Todo.org" "Tasks")
         "* TODO %?\n  %i\n  %a")
        ("j" "Journal" entry (file+olp+datetree "E:/emacs/0rg/Journal.org")
         "* %?\nEntered on %U\n %i\n %a")
        ("s" "Step" entry (file+headline "E:/Step.org" "Unsorted")
         "* %t\n%a\n%?")
        ("a" "Anki Basic" entry (file+headline org-my-anki-file "Dispatch")
         "* %U\n%a\n:PROPERTIES:\n:ANKI:NOTE_TYPE: Basic\n:ANKI_DECK: 0emacs\n:TAGS:\n:END:\n** Front\n\n** Back\n%?")
        ))

;; Org Settings
(setq org-tag-alist '(("GIR" . ?g) ("HO" . ?h) ("CardioPulmEndo" . ?c) ("NeuroPsy" . ?n)("MSK" . ?m)("Repro" . ?r))) 
(setq org-log-done 'time)
(setq org-my-anki-file "E:/emacs/0rg/Anki.org")
(setq org-capture-templates
;%^g prompts for tag
      '(("t" "Todo" entry (file+headline "E:/emacs/0rg/Todo.org" "Tasks")
         "* TODO %?\n  %i\n  %a")
        ("j" "Journal" entry (file+olp+datetree "E:/emacs/0rg/Journal.org")
         "* %?\nEntered on %U\n %i\n %a")
        ("s" "Step" entry (file+headline "E:/Step.org" "Unsorted")
         "* %t\n%a\n%?")
        ("a" "Anki Basic" entry (file+headline org-my-anki-file "Dispatch")
         "* %U\n%a\n:PROPERTIES:\n:ANKI:NOTE_TYPE: Basic\n:ANKI_DECK: 0emacs\n:TAGS:\n:END:\n** Front\n\n** Back\n%?")
        ))

;; Allow clipboard acccess
(setq x-select-enable-clipboard t
      x-select-enable-primary t)

(custom-set-variables
 ;; custom-set-variables was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 '(ansi-color-names-vector
   ["#242424" "#e5786d" "#95e454" "#cae682" "#8ac6f2" "#333366" "#ccaa8f" "#f6f3e8"])
 '(custom-enabled-themes (quote (light-blue)))
 '(global-visual-line-mode t)
 '(org-capture-templates
   (quote
    (("u" "Unsorted" entry
      (file+olp+datetree "~/org/Unsorted.emacs")
      "* %?
Entered on %U
 %i
 %a")
     ("t" "Todo" entry
      (file+headline "E:/emacs/0rg/Todo.org" "Tasks")
      "* TODO %?
  %i
  %a")
     ("j" "Journal" entry
      (file+olp+datetree "E:/emacs/0rg/Journal.org")
      "* %?
Entered on %U
 %i
 %a")
     ("s" "Step" entry
      (file+headline "E:/Step.org" "Unsorted")
      "* %t
%a
%?")
     ("a" "Anki Basic" entry
      (file+headline org-my-anki-file "Dispatch")
      "* %U
%a
:PROPERTIES:
:ANKI:NOTE_TYPE: Basic
:ANKI_DECK: 0emacs
:TAGS:
:END:
** Front

** Back
%?"))))
 '(org-insert-mode-line-in-empty-file t)
 '(org-modules
   (quote
    (org-bbdb org-bibtex org-docview org-gnus org-info org-irc org-mhe org-rmail org-w3m org-drill)))
 '(package-archives
   (quote
    (("gnu" . "http://elpa.gnu.org/packages/")
     ("melpa" . "https://melpa.org/packages/")
     ("gnu" . "https://elpa.gnu.org/packages/")
     ("org-learn" . "https://bitbucket.org/eeeickythump/org-drill/src/default/"))))
 '(package-selected-packages
   (quote
    (ivy read-aloud greader orgnav pdf-tools org-noter org-link-minor-mode org-starter anki-editor projectile closure-lint-mode cider))))
(custom-set-faces
 ;; custom-set-faces was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 )




