import React from 'react';
import { Box, Text } from 'ink';
import { KnowledgeDocument } from '../../knowledge/types.js';

interface DocumentBrowserProps {
  selectedDocument: KnowledgeDocument | null;
}

export const DocumentBrowser: React.FC<DocumentBrowserProps> = ({ selectedDocument }) => {
  return (
    <Box flexDirection="column" borderStyle="round" padding={1}>
      <Text>Document Browser</Text>
      {selectedDocument ? (
        <Box flexDirection="column">
          <Text>ID: {selectedDocument.id}</Text>
          <Text>Content: {selectedDocument.content}</Text>
        </Box>
      ) : (
        <Text>No document selected</Text>
      )}
    </Box>
  );
};
