<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    xmlns:ti="http://chs.harvard.edu/xmlns/cts"
    xmlns:dct="http://purl.org/dc/terms/"
    xmlns:cpt="http://purl.org/capitains/ns/1.0#"
    version="2.0">
    
    <xsl:output method="text" omit-xml-declaration="yes" indent="no"/>
    <xsl:param name="urn"><xsl:value-of select="/tei:TEI/tei:text/tei:body/tei:div/@n"/></xsl:param>
    
    <xsl:template match="/">
        <xsl:variable name="theText">
            <xsl:call-template name="extractText">
                <xsl:with-param name="text" select="/tei:TEI/tei:text/tei:body//tei:p"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="theLems">
            <xsl:call-template name="extractLem">
                <xsl:with-param name="text" select="//tei:w"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="dates">
            <xsl:call-template name="extractDates">
                <xsl:with-param name="date_tags" select="/tei:TEI/tei:text/tei:front/tei:dateline/tei:date"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:value-of select="normalize-space(/tei:TEI/tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title/text())"/>
        <xsl:text>*!</xsl:text>
        <xsl:text>*!</xsl:text>
        <xsl:text>&#13;******&#13;</xsl:text>
        <xsl:value-of select="$urn"/>
        <xsl:text>&#13;******&#13;</xsl:text>
        <xsl:choose>
            <xsl:when test="contains(lower-case(normalize-space(/tei:TEI/tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title/text())), 'formula')">
                <xsl:text>gte: ; lte: ; when: 0001</xsl:text>
            </xsl:when>
            <xsl:when test="$dates='' or $dates='?'">
                <xsl:text>gte: ; lte: ; when:</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$dates"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text>&#13;******&#13;</xsl:text>
        <!-- The outer replace function should include other text critical marks that should not get in the way of the search. -->
        <xsl:value-of select="normalize-space(replace(replace(replace($theText, ' ([\.,:;“])', '$1'), '(\[|&lt;)\s+', '$1'), '\s+(\]|&gt;)', '$1'))"/>
        <!--<xsl:value-of select="$theText"/>-->
        <xsl:text>&#13;******&#13;</xsl:text>
        <xsl:value-of select="replace($theLems, '\s+', ' ')"/>
    </xsl:template>
    
    <xsl:template name="extractText">
        <xsl:param name="text"/>
        <xsl:for-each select="$text">
            <xsl:value-of select="concat(replace(string-join(descendant-or-self::*[not(ancestor-or-self::tei:app) and not(ancestor-or-self::tei:note)]/text(), ''), '\s+', ' '), '&#13;')"/>
        </xsl:for-each>
    </xsl:template>
    
    <xsl:template name="extractLem">
        <xsl:param name="text"/>
        <xsl:for-each select="$text">
            <xsl:value-of select="./@lemma"/><xsl:text> </xsl:text>
        </xsl:for-each>
    </xsl:template>
    
    <xsl:template name="extractDates">
        <xsl:param name="date_tags"/>
        <xsl:for-each select="$date_tags">
            <xsl:text>gte</xsl:text>: <xsl:value-of select="./@notBefore"/>
            <xsl:text>; lte: </xsl:text><xsl:value-of select="./@notAfter"/>
            <xsl:text>; when: </xsl:text>
            <xsl:choose>
                <xsl:when test="./tei:date">
                    <xsl:for-each select="./tei:date"> 
                        <xsl:variable name="year_range" select="./@notBefore to ./@notAfter"/>
                        <xsl:variable name="date_when" select="./@when"/>
                        <xsl:for-each select="$year_range"><xsl:number format="0001" value="."/><xsl:text>-</xsl:text><xsl:value-of select="substring-after($date_when, '--')"/><xsl:text>,</xsl:text></xsl:for-each>
                    </xsl:for-each>
                </xsl:when>
                <xsl:otherwise><xsl:value-of select="./@when"/></xsl:otherwise>
            </xsl:choose>
            <xsl:text>&#13;</xsl:text>
        </xsl:for-each>
    </xsl:template>
    
    <!--<xsl:template match="tei:teiHeader"></xsl:template>-->
    
</xsl:stylesheet>