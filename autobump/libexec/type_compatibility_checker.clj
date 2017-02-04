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
;; Utility program that checks compatibility between two JVM types.
;; It prints the strings 'true' or 'false' depending on whether type A can
;; be substituted with type B.
;;
;; Usage: clojure inspector.clj [type-a] [type-b]
;;
;; This program is invoked by autobump's Clojure handler.

(ns autobump.handlers.clojure
  (:require [clojure.set :refer [union]]))

(defn- abort!
  "Exit from program immediately with an error message."
  [message & {exit-code :exit-code}]
  (let [exit-code (or exit-code 1)]
    (println (str "TypeCompatibilityChecker: " message))
    (System/exit exit-code)))

(defn- all-supers
  "Return a set of all supers of the type T."
  [t]
  (if (nil? t) #{} (apply union #{t} (map all-supers (supers t)))))

(defn- can-substitute?
  "Returns non-nil when A can be substituted with B."
  [a b]
  (if (or (nil? a) (nil? b))
    nil
    (some #{b} (all-supers a))))

(defn- safe-resolve
  [t]
  (if (nil? t) nil (resolve t)))

(defn main
  [args]
  (when (or (> (count args) 3)
            (< (count args) 2))
    (abort! "Invalid usage."))
  (if (= (count args) 3)
    (main (drop 1 args))
    (let [type-a (safe-resolve (read-string (first args)))
          type-b (safe-resolve (read-string (second args)))]
      (println (if (can-substitute? type-a type-b)
                 "true"
                 "false")))))

(main *command-line-args*)
