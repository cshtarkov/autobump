;; Utility program that inspects Clojure source files
;; and prints to stdout a representation of their APIs using
;; s-expressions in a format very similar to autobump's native format.
;;
;; Usage: clojure inspector.clj [files...]
;;
;; This program is invoked by autobump's Clojure handler.

(ns autobump.handlers.clojure)

(def public-fn-defs
  #{'defn
    'defmacro})

(def public-field-defs
  #{'def
    'defonce})

(defn- abort!
  "Exit from program immediately with an error message."
  [message & {exit-code :exit-code}]
  (let [exit-code (or exit-code 1)]
    (println (str "Inspector: " message))
    (System/exit exit-code)))

(defn- in?
  "Check membership in a collection."
  [coll elt]
  (some #{elt} coll))

(defn- index-in-seq
  "Return the first index where elt is found in coll."
  [coll elt]
  (->> coll                          ;; (a b c)
       (map-indexed list)            ;; ((0 a) (1 b) (2 c))
       (filter #(= elt (second %1))) ;; ((0 a))
       (first)                       ;; (0 a)
       (first)))                     ;; 0

(defn- read-source
  "Read in a Clojure source file and return a list of forms."
  [file-name]
  (read-string (str "(" (slurp file-name) ")")))

(defn- public-fn-def?
  "Check whether a form is a public function definition."
  [form]
  (let [form (first form)]
    (in? public-fn-defs form)))

(defn- public-field-def?
  "Check whether a form is a public definition."
  [form]
  (let [decl (first form)
        name (second form)]
    (and (in? public-field-defs decl)
         (not (:private (meta name))))))

(defn- get-ns
  "Returns the namespace in a list of forms."
  [forms]
  (let* [first-form (first forms)
         ns-form (when (= (first first-form) 'ns) first-form)]
    (when ns-form
      (second ns-form))))

(defn- name-of-def
  "Returns the name of a definition form."
  [def-form]
  (second def-form))

(defn- signatures
  "Returns a list of signatures of a function definition
  form."
  [function-form]
  (let [decl (resolve (first function-form))]
    (cond
      (= decl #'clojure.core/defn)
      (-> function-form ;; (defn myfunc ([a] nil) ([a b] nil))
          (macroexpand) ;; (def myfunc (fn ([a] nil) ([a b] nil)))
          (second)      ;; myfunc
          (meta)        ;; {:arglist (quote ([a] [a b]))}
          (:arglists)   ;; (quote ([a] [a b]))
          (second))     ;; ([a] [a b])
      (= decl #'clojure.core/defmacro)
      (-> function-form ;; (defmacro myfunc ([a] nil) ([a b] nil))
          (macroexpand) ;; (do (defn mm ([&form &env a] nil) ([&form &env a b] nil)) (. ...))
          (second)      ;; (defn mm ([&form &env a] nil) ([&form &env a b] nil))
          (signatures)))))

(defn- expand-tag
  "Given an argument, transform into a (argument type) pair."
  [arg]
  (cond
    (vector? arg) '(anon-vector nil)
    (map? arg) '(anon-map nil)
    true (list arg (:tag (meta arg)))))

(defn- expand-tags
  "Given a seq of arguments, transform each argument into a (argument type) pair."
  [args]
  (map expand-tag args))

(defn- destructure-arguments
  "Return a seq of argument names from argument bindings."
  [bindings]
  (cond
    (vector? bindings) bindings
    (map? bindings) (or (:keys bindings) (keys bindings))))

(defn- split-arguments
  "Return two seqs representing the positional
  and optional arguments in a signature."
  [signature]
  (let* [split      (split-at (or (index-in-seq signature '&) (count signature)) signature)
         positional (first split)
         optional   (destructure-arguments (second (second split)))]
    (list positional optional)))

(defn- describe-signature
  "Describe a signature as a sexp using only ()."
  [signature]
  (concat (list 'signature)
          (map expand-tags (split-arguments signature))))

(defn- describe-function
  "Describe a function as a sexp using only ()."
  [function-form]
  (list 'function
        (name-of-def function-form)
        (map describe-signature (signatures function-form))))

(defn- describe-field
  "Describe a field as a sexp using only ()."
  [field-form]
  (let [name (name-of-def field-form)]
    (list 'field
          name
          (:tag (meta name)))))

(defn- describe-file
  "Describe a file as a sexp using only ()."
  [file-name]
  (let* [forms         (read-source file-name)
         fields-defs   (filter public-field-def? forms)
         function-defs (filter public-fn-def? forms)]
    (list 'file
          (get-ns forms)
          (map describe-field fields-defs)
          (map describe-function function-defs))))

(defn describe-files
  "Describe a seq of files using only ()."
  [files]
  (map describe-file files))

(defn main
  "Main entry point of the program."
  [args]
  (when (empty? args)
    (abort! "Invalid number of arguments: expected [files...]"))
  (-> args
      (describe-files)
      (println)))

(main *command-line-args*)
