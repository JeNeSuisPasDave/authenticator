/* $Id: validate_rfcsearch.js,v 1.7 2008/11/18 18:49:01 cward Exp $ */
/* **************************************************************** *
 * These methods perform data validation of the RFC search forms    *
 * **************************************************************** */

var errString;

/**
 * Functiond does some basic data edits for the Errata Advanced Search
 * Form. Most of the work is actually to remove unused fields from the GET
 * string so that the URL looks nicer for users.
 */
function validateRFCSearchForm(fields) {
   var errCount  = 0;
   errString = new String("Please correct these input errors:\n");

   if (fields.rfc.value.length > 0) {
      // Validate this value: must be all digits
      if (isNaN(fields.rfc.value)) {
         errString = errString.concat("\tThe RFC number may contain only digits.\n");
         errCount++;
      }
   }

   if (fields.eid.value.length > 0) {
      // Validate this value: must be all digits
      if (isNaN(fields.eid.value)) {
         errString = errString.concat("\tThe errata id may only contain digits.\n");
         errCount++;
      }
   }

   if (fields.submit_date.value.length > 0) {
      errCount += validateDateString(fields.submit_date.value);
   }

   if (errCount > 0) {
      alert(errString);
      return false;             // Cancel the form submit
   }

   // Everything we checked validated. Now go through and remove unused
   // arguments so that the URL doesn't look to ugly.
   if (fields.rfc.value.length <= 0) {
      el = document.getElementById(fields.rfc.id);
      el.parentNode.removeChild(el); // remore "rfc"
   }

   if (fields.eid.value.length <= 0) {
      el = document.getElementById(fields.eid.id);
      el.parentNode.removeChild(el); // remove "eid"
   }

   if (fields.submit_date.value.length <= 0) {
      el = document.getElementById(fields.submit_date.id);
      el.parentNode.removeChild(el); // remove "submit_date"
   } 

   if (fields.rec_status.value.length <= 0) {
      el = document.getElementById(fields.rec_status.id);
      el.parentNode.removeChild(el); // remove "rec_status"
   }

   if (fields.area_acronym.value.length <= 0) {
      el = document.getElementById(fields.area_acronym.id);
      el.parentNode.removeChild(el); // remove "area_acronym"
   }

   if (fields.errata_type.value.length <= 0) {
      el = document.getElementById(fields.errata_type.id);
      el.parentNode.removeChild(el); // remove "errata_type"
   }

   if (fields.wg_acronym.value.length <= 0) {
      el = document.getElementById(fields.wg_acronym.id);
      el.parentNode.removeChild(el); // remove "wg_acronym"
   }

   if (fields.submitter_name.value.length <= 0) {
      el = document.getElementById(fields.submitter_name.id);
      el.parentNode.removeChild(el); // remove "submitter_name"
   }

   if (fields.stream_name.value.length <= 0) {
      el = document.getElementById(fields.stream_name.id);
      el.parentNode.removeChild(el); // remove "stream_name"
   }

   if (fields.eid.value.length > 0) {
      el = document.getElementById(fields.rec_status.id);
      if (el != null) {
         el.parentNode.removeChild(el); // remove "rec_status"
      }
      if (!fields.presentation.id) {
         el = document.getElementById(fields.presentationT.id);
         if (el != null ) { 
            el.parentNode.removeChild(el);
         }
         el = document.getElementById(fields.presentationR.id);
         if (el != null ) { 
            el.parentNode.removeChild(el);
         }
      } else {
         el = document.getElementById(fields.presentation.id);
         el.parentNode.removeChild(el);
      }
   }

   return true;                 // Let form go to server
}

/**
 * Validate the field of the form used to select a RFC document for reporting
 * of new errrata.
 * Form "report" in errata.php.
 */
function validateRFCNewErrataForm(fields) {
   var errCount  = 0;
   errString = new String("Please correct these input errors:\n");
   errCount = validateAddSearch(fields);
   if (errCount > 0) {
      alert(errString);
      return false;             // Cancel the form submit
   }
   return true;                 // Let form go to server
}

function validateAddSearch(fields) {
   var count = 0;

  if (fields.rfc.value.length <= 0 ) {
      errString = errString.concat("\tPlease provide the number for the RFC.\n");
      count++;
   } 

   if (fields.rfc.value.length > 0 && isNaN(fields.rfc.value)) {
      errString = errString.concat("\tThe RFC number may contain only digits.\n");
      count++;
   }

   return count;
}

/*
 * Check that the date string is in a format useful to MySQL (or whatever)
 * database.
 */
var YMD = new RegExp('\\d\\d\\d\\d-\\d\\d-\\d\\d');
var YM  = new RegExp('\\d\\d\\d\\d-\\d\\d');
var Yonly = new RegExp('\\d\\d\\d\\d');
function validateDateString(date) {
   if (YMD.test(date)) {
      return 0;
   }
   if (YM.test(date)) {
      return 0;
   }
   if (Yonly.test(date)) {
      return 0;
   }
   errString = errString.concat("\tDates must be in YYYYY-MM-DD format.\n");
   return 1;
}

/*
 * Set the fields of the Errata Advanced Search Form to default values. The
 * usual "reset" method of the HTML Forms object uses the values set when the
 * form got created. When previously entered data is carried over after a
 * search executes, that data is seen as the "reset" values instead of the
 * values in a completely new instance of the form.
 * 
 * BWR: The "rec_status" values are hardcoded here; however, these MUST match
 * the constants defined in errata_lib.php for those values.
 */
function clearAdvSearchForm(fields) {
   fields.rfc.value = "";
   fields.eid.value = "";
   fields.area_acronym.value = "";
   fields.errata_type.value = "";
   fields.wg_acronym.value = "";
   fields.submitter_name.value = "";
   fields.stream_name.value = "";
   fields.submit_date.value = "";
   fields.rec_status.value = 15; // Any/All user side
   if (fields.presentation.length > 1) { // undefined for verifier side
      fields.presentation[0].checked = true; // the "table" node
   } else {
// Reported for verifier side
      fields.rec_status.value = 2;
   }
   fields.rfc.focus();
   return true;
}

function clearAdvSearchFormVerify(fields) {
   clearAdvSearchForm(fields);  // do basic clear
   // Additional settings for verifier side.

}
/**
 * Step through the fields of a reported erratum. Return false if anything
 * looks odd, else true.
 * Called by onsubmit event of errata_report form.
 */
function validateRFCEditSearchForm(fields) {
   var errCount  = 0;
   errString = new String("Please correct these input errors:\n");

   // Use the existance of the eid field to detect that the form allows
   // either a RFC number or an errata id as the selection criterion. If
   // present, validate that form, else assume the form only has the RFC 
   // number (i.e. comes from the "Report New Errata" form).
   if (!(fields.eid === undefined)) {
      errCount += validateEditSearch(fields);
      if (errCount == 0) { 
         // If there were no errors, remove from the element the unused
         // parameter so that the GET method won't write an empty parameter
         // in the browser URL display window.
         if (fields.rfc.value.length <= 0)  {
            el = document.getElementById(fields.rfc.id);
            el.parentNode.removeChild(el); // remore "rfc"
         } else {
            el = document.getElementById(fields.eid.id);
            el.parentNode.removeChild(el); // remove "eid"
         }
      }
   } else {
      errCount += validateAddSearch(fields); // didn't have an errata id
   }
         
   if (errCount > 0) {
      alert(errString);
      return false;             // Cancel the form submit
   }
   return true;                 // Let form go to server
}

function validateEditSearch(fields) {
   var count = 0;

   if (fields.rfc.value.length <= 0 && fields.eid.value.length <= 0 ) {
      errString = errString.concat("\tPlease provide the number for the RFC or report.\n");
      count++;
   } 

   if (fields.rfc.value.length > 0 && isNaN(fields.rfc.value)) {
      errString = errString.concat("\tThe RFC number may contain only digits.\n");
      count++;
   }

   if (fields.eid.value.length > 0 && isNaN(fields.eid.value)) {
      errString = errString.concat("\tThe errata id may only contain digits.\n");
      count++;
   }
   return count;
}

function validateEditAddSearch(fields) {
   var count = 0;

  if (fields.rfc.value.length <= 0 ) {
      errString = errString.concat("\tPlease provide the number for the RFC.\n");
      count++;
   } 

   if (fields.rfc.value.length > 0 && isNaN(fields.rfc.value)) {
      errString = errString.concat("\tThe RFC number may contain only digits.\n");
      count++;
   }

   return count;
}
