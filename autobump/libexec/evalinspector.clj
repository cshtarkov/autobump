;; Copyright 2016-2017 Christian Shtarkov
;;
;; This file is part of Autobump.
;;
;; This program is free software; you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation; either version 3 of the License, or
;; (at your option) any later version.
;;
;; This program is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.
;;
;; You should have received a copy of the GNU General Public License
;; along with this program; if not, see <http://www.gnu.org/licenses/>.
;;
;; Description:
;;
;; Utility program that inspects Clojure source files
;; and prints to stdout a representation of their APIs using
;; s-expressions in a format very similar to autobump's native format.
;;
;; Usage: clojure inspector.clj [files...]
;;
;; This program is invoked by autobump's Clojure handler.

(ns autobump.handlers.clojure)

(def form-whitelist
  #{'ns
    'def
    'defmacro
    'definline
    'defn
    'defonce
    'ann
    'ann-form})

(defn- abort!
  "Exit from program immediately with an error message."
  [message & {exit-code :exit-code}]
  (let [exit-code (or exit-code 1)]
    (println (str "Inspector: " message))
    (System/exit exit-code)))

(defn- not-this-file
  "Predicate that matches all file names except this program."
  [file]
  (not (= (:file (meta #'not-this-file)) file)))

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

(defn- basename
  "Return the basename of a symbol, i.e. strip the prefix."
  [s]
  (symbol (name s)))

(defn- read-source
  "Read in a Clojure source file and return a list of forms."
  [file-name]
  (read-string (str "(" (slurp file-name) ")")))

(defn- form-safe?
  "Check whether a form is safe for evaluation."
  [form]
  (let* [decl (first form)
         base-decl (basename decl)]
    (in? form-whitelist base-decl)))

(defn- safe-eval
  "Safely evaluate only whitelisted forms."
  ([form]
   (when (form-safe? form)
     (eval form))))

(defn- get-ns
  "Returns the namespace in a list of forms."
  [forms]
  (let* [first-form (first forms)
         ns-form (when (= (first first-form) 'ns) first-form)]
    (when ns-form
      (second ns-form))))

(defn- symbols-in-ns
  "Get a list of publicly defined symbols in the current namespace."
  [ns]
  (require ns)
  (keys (ns-publics ns)))

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

(defn- signatures
  "Return the signatures of a function."
  [symbol]
  (:arglists (meta symbol)))

(defn- describe-signature
  "Describe a signature as a sexp using only ()."
  [signature]
  (concat (list 'signature)
          (map expand-tags (split-arguments signature))))

(defn- describe-function
  "Describe a function as a sexp using only ()."
  [{name :name qname :qname function :var}]
  (list 'function
        name
        (map describe-signature (signatures qname))))

(defn- describe-field
  "Describe a field as a sexp using only ()."
  [{name :name qname :qname value :var}]
  (list 'field
        name
        (type value)))

(defn- safe-eval-file
  "Safely evaluate forms in a file and returns its namespace."
  [file-name]
  (let* [forms (read-source file-name)
         namespace (get-ns forms)]
    (map safe-eval forms)
    namespace))

(defn- describe-ns
  "Describe a file as a sexp using only ()."
  [namespace]
  (let* [vars (map
               (fn [s]
                 (let [resolved (ns-resolve namespace s)]
                   {:name s
                    :qname resolved
                    :var (var-get resolved)}))
               (symbols-in-ns namespace))
         fields (filter (fn [p] (not (fn? (:var p)))) vars)
         functions (filter (fn [p] (fn? (:var p))) vars)]
    (list 'file
          namespace
          (map describe-field fields)
          (map describe-function functions))))

(defn describe-files
  "Describe a seq of files using only ()."
  [files]
  (map describe-ns (map safe-eval-file (filter not-this-file files))))

(defn main
  "Main entry point of the program."
  [args]
  (when (empty? args)
    (abort! "Invalid number of arguments: expected [files...]"))
  (-> args
      (describe-files)
      (println)))

(main *command-line-args*)
